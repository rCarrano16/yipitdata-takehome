"""FastMCP server: the KPI estimates data API exposed as MCP tools.

This is the AI-agent channel of the application. An LLM client (Claude Desktop,
Cursor, and similar) connects over stdio and calls these seven read-only tools
to look up companies, retrieve KPI estimates, query quarter-to-date (QTD) data,
and compare a KPI across companies. The server also exposes two MCP prompts,
reusable templates that chain the tools into a common analyst workflow.

The tools reuse the backend service layer in-process: they import `app.service`
and call the exact same functions the REST routers call, so query logic is
written once and never duplicated, with no HTTP hop to the REST API. Each tool
opens its own short-lived, read-only database session via `read_only_session`,
which rolls back instead of committing, so the read-only server is read-only by
construction.

Each tool is annotated with a Pydantic return type, so FastMCP generates a JSON
Schema for the tool output as well as its input. That output schema is the
formal description of the result shape, which is what lets a calling LLM
discover what it gets back. Four tools return existing service-layer schemas
(`CompanyDetail`, `SeriesDetail`, `CompanyEstimates`, `KpiComparison`); the
other three return small wrapper models defined here, because the MCP protocol
requires a tool output schema to be an object, not a bare array or scalar.

stdio note: with stdio transport the process stdout IS the JSON-RPC channel, so
nothing else may be written there. This module therefore never imports
`app.main` (importing it would call `configure_logging()`, which installs a
stdout log handler) and configures no logging of its own. FastMCP logs to
stderr, which stdio leaves free.
"""

from datetime import date

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from pydantic import BaseModel

from app import service
from app.db import read_only_session
from app.errors import NotFoundError
from app.schemas import (
    CompanyDetail,
    CompanyEstimates,
    CompanySummary,
    KpiComparison,
    KpiInfo,
    QtdSnapshot,
    SeriesDetail,
)

# ---------------------------------------------------------------------------
# Tool result models
#
# The MCP protocol requires a tool output schema to be a JSON object. Three
# tools already return object-typed service schemas (CompanyDetail, SeriesDetail,
# CompanyEstimates) and need no wrapper. The three models below wrap results that
# would otherwise be a bare list or an ad-hoc shape, so every tool advertises a
# clean, object-typed output schema. They are MCP-specific (the REST API returns
# bare arrays for the list endpoints), so they live here, not in app/schemas.py.
# ---------------------------------------------------------------------------


class CompanyList(BaseModel):
    """The result of search_companies: the companies that matched."""

    companies: list[CompanySummary]


class KpiList(BaseModel):
    """The result of list_kpis: every KPI and the unit it is measured in."""

    kpis: list[KpiInfo]


class CurrentQtd(BaseModel):
    """The result of get_current_qtd: the latest QTD snapshot for one series.

    `current_qtd` is null when the series has no QTD data.
    """

    ticker: str
    kpi: str
    unit: str
    current_qtd: QtdSnapshot | None


mcp = FastMCP(
    name="kpi-estimates",
    version="0.1.0",
    instructions=(
        "Read-only access to quarterly KPI estimates for public companies, the "
        "same data the investor web portal is built on.\n\n"
        "Each (company, KPI) pair is a time series with two parts:\n"
        "- history: one value per closed fiscal quarter.\n"
        "- QTD (quarter-to-date): several intra-quarter snapshots of the "
        "in-progress quarter, each stamped with an `as_of` date. The current QTD "
        "value is the snapshot with the latest `as_of`.\n\n"
        "Identifiers are resolved case-insensitively. To get valid identifiers, "
        "call `search_companies` for tickers and `list_kpis` for KPI names "
        "before calling the estimate tools.\n\n"
        "Data coverage: closed-quarter history runs 2022Q1 through 2025Q4; QTD "
        "snapshots exist only for the current quarter, 2026Q1."
    ),
    # Mask the details of unexpected errors (for example a database error that
    # could carry a connection string). Errors raised deliberately as ToolError
    # are always shown; this only affects exceptions that were not anticipated.
    mask_error_details=True,
)

# Every tool is a pure read against the project's own database. These MCP
# annotations state that explicitly: a client (for example Claude Desktop) reads
# them to decide whether a call is safe to run without asking the user first.
# All four hints are truthful for a read-only query over a fixed data set.
_READ_ONLY_ANNOTATIONS = {
    "readOnlyHint": True,
    "destructiveHint": False,
    "idempotentHint": True,
    "openWorldHint": False,
}


def _require_ordered_dates(date_from: date | None, date_to: date | None) -> None:
    """Reject an inverted date range before it reaches the service layer.

    A date_from later than date_to is almost certainly a caller mistake. The
    service layer would simply return an empty result, which a calling LLM could
    misread as "no data exists". Failing loudly with a ToolError is clearer.
    """
    if date_from is not None and date_to is not None and date_from > date_to:
        raise ToolError(f"date_from ({date_from}) must not be after date_to ({date_to})")


@mcp.tool(annotations=_READ_ONLY_ANNOTATIONS)
def search_companies(query: str | None = None) -> CompanyList:
    """Find companies by ticker, name, or sector.

    Use this to discover which companies exist and to get the exact ticker the
    other tools expect. With no query it returns every company.

    Args:
        query: Optional case-insensitive text matched against ticker, company
            name, and sector. Omit it to list all companies.
    """
    with read_only_session() as session:
        companies = service.list_companies(session, search=query)
    return CompanyList(companies=companies)


@mcp.tool(annotations=_READ_ONLY_ANNOTATIONS)
def list_kpis() -> KpiList:
    """List every KPI and the unit its values are measured in.

    Use this to get the exact KPI names the estimate tools expect, for example
    "Total Revenue ($MM)" or "ASP ($)".
    """
    with read_only_session() as session:
        kpis = service.list_kpis(session)
    return KpiList(kpis=kpis)


@mcp.tool(annotations=_READ_ONLY_ANNOTATIONS)
def get_company(ticker: str) -> CompanyDetail:
    """Get one company profile and the list of KPIs it reports.

    Use this after `search_companies` to see which KPIs a company has before
    requesting its estimates. It returns the company profile and KPI list, not
    the estimate values: use `get_company_estimates` or `get_kpi_estimates` for
    those.

    Args:
        ticker: The company ticker, case-insensitive, for example "ACME".
    """
    try:
        with read_only_session() as session:
            return service.get_company(session, ticker)
    except NotFoundError as e:
        raise ToolError(str(e)) from e


@mcp.tool(annotations=_READ_ONLY_ANNOTATIONS)
def get_company_estimates(
    ticker: str,
    date_from: date | None = None,
    date_to: date | None = None,
) -> CompanyEstimates:
    """Get every KPI estimate series for one company in a single call.

    Returns one full series per KPI the company reports, each with its
    closed-quarter history and its QTD snapshots. Use this for a company-wide
    view; use `get_kpi_estimates` when you only need one specific KPI.

    Args:
        ticker: The company ticker, case-insensitive, for example "ACME".
        date_from: Optional inclusive lower bound as an ISO date (YYYY-MM-DD).
            History is filtered by quarter-end date, QTD snapshots by `as_of`.
        date_to: Optional inclusive upper bound as an ISO date (YYYY-MM-DD).
    """
    _require_ordered_dates(date_from, date_to)
    try:
        with read_only_session() as session:
            return service.get_company_estimates(session, ticker, date_from, date_to)
    except NotFoundError as e:
        raise ToolError(str(e)) from e


@mcp.tool(annotations=_READ_ONLY_ANNOTATIONS)
def get_kpi_estimates(
    ticker: str,
    kpi: str,
    date_from: date | None = None,
    date_to: date | None = None,
) -> SeriesDetail:
    """Get the full estimate history and QTD snapshots for one company KPI.

    Returns the closed-quarter history, every QTD snapshot of the in-progress
    quarter (each with its `as_of` date), and the current QTD value. This is the
    detailed series behind the portal's history-vs-QTD chart.

    Args:
        ticker: The company ticker, case-insensitive, for example "ACME".
        kpi: The KPI name, case-insensitive, for example "Total Revenue ($MM)".
            Call `list_kpis` for the available names.
        date_from: Optional inclusive lower bound as an ISO date (YYYY-MM-DD).
            History is filtered by quarter-end date, QTD snapshots by `as_of`.
        date_to: Optional inclusive upper bound as an ISO date (YYYY-MM-DD).
    """
    _require_ordered_dates(date_from, date_to)
    try:
        with read_only_session() as session:
            return service.get_series(session, ticker, kpi, date_from, date_to)
    except NotFoundError as e:
        raise ToolError(str(e)) from e


@mcp.tool(annotations=_READ_ONLY_ANNOTATIONS)
def get_current_qtd(ticker: str, kpi: str) -> CurrentQtd:
    """Get only the current quarter-to-date (QTD) estimate for one company KPI.

    Returns the single most recent QTD snapshot, the one with the latest `as_of`
    date. Use this when you only need the latest in-progress-quarter value, not
    the full history. `current_qtd` is null if the series has no QTD data.

    Args:
        ticker: The company ticker, case-insensitive, for example "ACME".
        kpi: The KPI name, case-insensitive, for example "Total Revenue ($MM)".
            Call `list_kpis` for the available names.
    """
    try:
        with read_only_session() as session:
            series = service.get_series(session, ticker, kpi)
    except NotFoundError as e:
        raise ToolError(str(e)) from e
    return CurrentQtd(
        ticker=series.ticker,
        kpi=series.kpi,
        unit=series.unit,
        current_qtd=series.current_qtd,
    )


@mcp.tool(annotations=_READ_ONLY_ANNOTATIONS)
def compare_kpi_across_companies(
    kpi: str,
    tickers: list[str] | None = None,
) -> KpiComparison:
    """Compare one KPI across several companies, side by side.

    Returns one row per company with its latest closed-quarter value, its
    current QTD value, and its QoQ and YoY trend signals, so peers can be ranked
    on a single metric in one call. Use this for a peer or sector comparison;
    use `get_kpi_estimates` when you need the full history of one company.

    Call `search_companies` first to get the exact tickers (for example every
    company in one sector), then pass them here. Omit `tickers` to compare every
    company that reports the KPI.

    Args:
        kpi: The KPI name, case-insensitive, for example "Total Revenue ($MM)".
            Call `list_kpis` for the available names.
        tickers: Optional list of company tickers, case-insensitive. Omit it to
            include every company that reports the KPI.
    """
    try:
        with read_only_session() as session:
            return service.compare_kpi(session, kpi, tickers)
    except NotFoundError as e:
        raise ToolError(str(e)) from e


# ---------------------------------------------------------------------------
# Prompts
#
# MCP prompts are reusable, parameterized templates the client surfaces to the
# user (Claude Desktop shows them as selectable starters). Each one chains the
# tools above into a common analyst workflow, so an agent follows a known-good
# sequence of calls instead of improvising one.
# ---------------------------------------------------------------------------


@mcp.prompt
def earnings_preview(ticker: str) -> str:
    """Draft a pre-earnings briefing for one company from its KPI estimates."""
    return (
        f"Prepare a concise earnings-preview briefing for {ticker}.\n\n"
        "Steps:\n"
        f'1. Call get_company with ticker "{ticker}" to see which KPIs it '
        "reports.\n"
        f'2. Call get_company_estimates for "{ticker}" to pull every KPI '
        "series.\n"
        "3. For each KPI, state the latest closed-quarter value, the current "
        "QTD estimate with its as_of date, and the QoQ and YoY trend.\n"
        "4. Flag any KPI where the QTD pace looks notably ahead of or behind "
        "the recent historical trend.\n\n"
        "Present it as a short briefing an investor can read in under a minute."
    )


@mcp.prompt
def peer_scan(kpi: str, sector: str | None = None) -> str:
    """Compare one KPI across a sector or peer group, ranked by standing and trend."""
    group = f"companies in the {sector} sector" if sector else "a peer group of companies"
    search_hint = f' with query "{sector}"' if sector else ""
    return (
        f'Compare {group} on the KPI "{kpi}".\n\n'
        "Steps:\n"
        f"1. Call search_companies{search_hint} to get the company tickers.\n"
        f'2. Call compare_kpi_across_companies with kpi "{kpi}" and those '
        "tickers.\n"
        "3. Rank the companies by their current QTD value, and call out the "
        "strongest and weakest QoQ and YoY movers.\n\n"
        "Present a short comparative table plus a one-line takeaway."
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")
