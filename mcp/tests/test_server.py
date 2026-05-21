"""Tests for the MCP server: tool registration and the MCP-specific glue.

The tests drive the server through an in-memory fastmcp.Client, so the real
FastMCP machinery runs: tool dispatch, argument coercion, output-schema
handling, and the wrapping of a raised exception into an MCP error. The backend
service layer is stubbed (see conftest), so the tests need no database and are
fully deterministic. The service layer's own behavior is covered by the backend
suite; these tests own the MCP boundary: the NotFoundError -> ToolError
translation, the result wrapper models, and the get_current_qtd projection.
"""

import asyncio
from datetime import date, datetime

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

import server
from app.errors import NotFoundError
from app.schemas import (
    CompanyDetail,
    CompanyEstimates,
    CompanySummary,
    EstimatePoint,
    KpiInfo,
    QtdSnapshot,
    SeriesDetail,
)

_TOOL_NAMES = {
    "search_companies",
    "list_kpis",
    "get_company",
    "get_company_estimates",
    "get_kpi_estimates",
    "get_current_qtd",
}


def _list_tools():
    """Return the tool list as an MCP client sees it."""

    async def _run():
        async with Client(server.mcp) as client:
            return await client.list_tools()

    return asyncio.run(_run())


def _call_tool(name, args):
    """Call one tool through an in-memory MCP client and return the result."""

    async def _run():
        async with Client(server.mcp) as client:
            return await client.call_tool(name, args)

    return asyncio.run(_run())


_QTD = QtdSnapshot(
    period="2026Q1",
    period_start=date(2026, 1, 1),
    period_end=date(2026, 3, 31),
    value=42.0,
    as_of=date(2026, 3, 15),
    created_at=datetime(2026, 5, 1, 12, 0, 0),
)


def _series(*, current_qtd: QtdSnapshot | None) -> SeriesDetail:
    """A minimal SeriesDetail for stubbing service.get_series."""
    history = [
        EstimatePoint(
            period="2025Q4",
            period_start=date(2025, 10, 1),
            period_end=date(2025, 12, 31),
            value=120.0,
            created_at=datetime(2026, 5, 1, 12, 0, 0),
        )
    ]
    return SeriesDetail(
        ticker="ACME",
        company_name="Acme Inc",
        kpi="Total Revenue ($MM)",
        unit="$MM",
        history=history,
        qtd_snapshots=[current_qtd] if current_qtd is not None else [],
        current_qtd=current_qtd,
        last_updated=datetime(2026, 5, 1, 12, 0, 0),
    )


# --- tool registration -----------------------------------------------------


def test_all_tools_are_registered():
    assert {t.name for t in _list_tools()} == _TOOL_NAMES


def test_every_tool_declares_read_only_annotations():
    for tool in _list_tools():
        assert tool.annotations is not None, tool.name
        assert tool.annotations.readOnlyHint is True, tool.name
        assert tool.annotations.destructiveHint is False, tool.name
        assert tool.annotations.idempotentHint is True, tool.name
        assert tool.annotations.openWorldHint is False, tool.name


def test_every_tool_publishes_an_object_output_schema():
    for tool in _list_tools():
        assert tool.outputSchema is not None, tool.name
        assert tool.outputSchema.get("type") == "object", tool.name


# --- search_companies ------------------------------------------------------


def test_search_companies_wraps_results_and_passes_the_query(monkeypatch):
    seen = {}

    def fake_list_companies(session, search=None):
        seen["search"] = search
        return [CompanySummary(ticker="ACME", name="Acme Inc", sector="Cloud")]

    monkeypatch.setattr(server.service, "list_companies", fake_list_companies)
    result = _call_tool("search_companies", {"query": "acme"})

    assert seen["search"] == "acme"
    assert result.structured_content == {
        "companies": [{"ticker": "ACME", "name": "Acme Inc", "sector": "Cloud"}]
    }


def test_search_companies_without_a_query_passes_none(monkeypatch):
    seen = {}

    def fake_list_companies(session, search=None):
        seen["search"] = search
        return []

    monkeypatch.setattr(server.service, "list_companies", fake_list_companies)
    result = _call_tool("search_companies", {})

    assert seen["search"] is None
    assert result.structured_content == {"companies": []}


# --- list_kpis -------------------------------------------------------------


def test_list_kpis_wraps_results(monkeypatch):
    monkeypatch.setattr(
        server.service, "list_kpis", lambda session: [KpiInfo(name="ASP ($)", unit="$")]
    )
    result = _call_tool("list_kpis", {})
    assert result.structured_content == {"kpis": [{"name": "ASP ($)", "unit": "$"}]}


# --- get_company -----------------------------------------------------------


def test_get_company_returns_the_company(monkeypatch):
    detail = CompanyDetail(
        ticker="ACME",
        name="Acme Inc",
        sector="Cloud",
        kpis=[KpiInfo(name="ASP ($)", unit="$")],
    )
    monkeypatch.setattr(server.service, "get_company", lambda session, ticker: detail)
    result = _call_tool("get_company", {"ticker": "ACME"})
    assert result.structured_content == detail.model_dump(mode="json")


def test_get_company_unknown_ticker_raises_tool_error(monkeypatch):
    def fake_get_company(session, ticker):
        raise NotFoundError(f"company not found: {ticker}")

    monkeypatch.setattr(server.service, "get_company", fake_get_company)
    with pytest.raises(ToolError, match="company not found: NOPE"):
        _call_tool("get_company", {"ticker": "NOPE"})


# --- get_company_estimates -------------------------------------------------


def test_get_company_estimates_returns_every_series_and_passes_dates(monkeypatch):
    seen = {}

    def fake_get_company_estimates(session, ticker, date_from=None, date_to=None):
        seen.update(ticker=ticker, date_from=date_from, date_to=date_to)
        return CompanyEstimates(
            ticker="ACME",
            company_name="Acme Inc",
            sector="Cloud",
            series=[_series(current_qtd=_QTD)],
        )

    monkeypatch.setattr(server.service, "get_company_estimates", fake_get_company_estimates)
    result = _call_tool(
        "get_company_estimates",
        {"ticker": "ACME", "date_from": "2025-01-01", "date_to": "2025-12-31"},
    )

    assert seen["ticker"] == "ACME"
    # FastMCP coerces the ISO date strings to date objects before the tool runs.
    assert seen["date_from"] == date(2025, 1, 1)
    assert seen["date_to"] == date(2025, 12, 31)
    assert result.structured_content["ticker"] == "ACME"
    assert len(result.structured_content["series"]) == 1


def test_get_company_estimates_unknown_ticker_raises_tool_error(monkeypatch):
    def fake_get_company_estimates(session, ticker, date_from=None, date_to=None):
        raise NotFoundError(f"company not found: {ticker}")

    monkeypatch.setattr(server.service, "get_company_estimates", fake_get_company_estimates)
    with pytest.raises(ToolError, match="company not found: NOPE"):
        _call_tool("get_company_estimates", {"ticker": "NOPE"})


def test_get_company_estimates_inverted_date_range_raises_tool_error():
    with pytest.raises(ToolError, match="must not be after"):
        _call_tool(
            "get_company_estimates",
            {"ticker": "ACME", "date_from": "2025-12-31", "date_to": "2025-01-01"},
        )


# --- get_kpi_estimates -----------------------------------------------------


def test_get_kpi_estimates_returns_the_series_and_passes_the_dates(monkeypatch):
    seen = {}

    def fake_get_series(session, ticker, kpi_name, date_from=None, date_to=None):
        seen.update(ticker=ticker, kpi=kpi_name, date_from=date_from, date_to=date_to)
        return _series(current_qtd=_QTD)

    monkeypatch.setattr(server.service, "get_series", fake_get_series)
    result = _call_tool(
        "get_kpi_estimates",
        {
            "ticker": "ACME",
            "kpi": "Total Revenue ($MM)",
            "date_from": "2025-01-01",
            "date_to": "2025-12-31",
        },
    )

    assert seen["ticker"] == "ACME"
    assert seen["kpi"] == "Total Revenue ($MM)"
    # FastMCP coerces the ISO date strings to date objects before the tool runs.
    assert seen["date_from"] == date(2025, 1, 1)
    assert seen["date_to"] == date(2025, 12, 31)
    assert result.structured_content == _series(current_qtd=_QTD).model_dump(mode="json")


def test_get_kpi_estimates_unknown_series_raises_tool_error(monkeypatch):
    def fake_get_series(session, ticker, kpi_name, date_from=None, date_to=None):
        raise NotFoundError(f"KPI not found: {kpi_name}")

    monkeypatch.setattr(server.service, "get_series", fake_get_series)
    with pytest.raises(ToolError, match="KPI not found"):
        _call_tool("get_kpi_estimates", {"ticker": "ACME", "kpi": "Nope"})


def test_get_kpi_estimates_inverted_date_range_raises_tool_error():
    with pytest.raises(ToolError, match="must not be after"):
        _call_tool(
            "get_kpi_estimates",
            {
                "ticker": "ACME",
                "kpi": "Total Revenue ($MM)",
                "date_from": "2025-12-31",
                "date_to": "2025-01-01",
            },
        )


# --- get_current_qtd -------------------------------------------------------


def test_get_current_qtd_projects_the_latest_snapshot(monkeypatch):
    monkeypatch.setattr(server.service, "get_series", lambda *a, **k: _series(current_qtd=_QTD))
    result = _call_tool("get_current_qtd", {"ticker": "ACME", "kpi": "Total Revenue ($MM)"})
    content = result.structured_content
    assert content["ticker"] == "ACME"
    assert content["kpi"] == "Total Revenue ($MM)"
    assert content["unit"] == "$MM"
    assert content["current_qtd"] == _QTD.model_dump(mode="json")


def test_get_current_qtd_is_null_when_the_series_has_no_qtd(monkeypatch):
    monkeypatch.setattr(server.service, "get_series", lambda *a, **k: _series(current_qtd=None))
    result = _call_tool("get_current_qtd", {"ticker": "ACME", "kpi": "Units Sold"})
    assert result.structured_content["current_qtd"] is None


def test_get_current_qtd_unknown_series_raises_tool_error(monkeypatch):
    def fake_get_series(session, ticker, kpi_name, date_from=None, date_to=None):
        raise NotFoundError(f"company not found: {ticker}")

    monkeypatch.setattr(server.service, "get_series", fake_get_series)
    with pytest.raises(ToolError, match="company not found"):
        _call_tool("get_current_qtd", {"ticker": "ZZZ", "kpi": "ASP ($)"})
