"""The shared service layer: every KPI and QTD query lives here, exactly once.

Both consumers, the FastAPI REST routers and the FastMCP server, import these
functions. That is the structural answer to "one shared data API": the query
logic is written once and never duplicated.

Each function takes a SQLAlchemy `Session` as its first argument and returns
Pydantic models, so both consumers get identical, typed results. The service
layer does not open, commit, or close the session, and it does not import
`app.db`: the caller owns the session and the transaction. That keeps the layer
pure and trivially testable against any engine.
"""

import logging
from collections import defaultdict
from datetime import date, datetime

from sqlalchemy import Row, func, select
from sqlalchemy.orm import Session

from app.errors import NotFoundError
from app.models import Company, Estimate, Kpi
from app.schemas import (
    CompanyDetail,
    CompanyEstimates,
    CompanySummary,
    EstimatePoint,
    EstimateRecord,
    KpiInfo,
    OverviewCard,
    OverviewResponse,
    PublishEstimateRequest,
    QtdSnapshot,
    SeriesDetail,
)

logger = logging.getLogger("app.service")

# How many recent historical values each overview card's sparkline shows.
_SPARKLINE_POINTS = 8


# ---------------------------------------------------------------------------
# Lookups
# ---------------------------------------------------------------------------


def _get_company(session: Session, ticker: str) -> Company:
    """Return the company for a ticker, or raise NotFoundError. Case-insensitive."""
    company = session.scalar(select(Company).where(func.lower(Company.ticker) == ticker.lower()))
    if company is None:
        raise NotFoundError(f"company not found: {ticker}")
    return company


def _get_kpi(session: Session, kpi_name: str) -> Kpi:
    """Return the KPI for a name, or raise NotFoundError."""
    kpi = session.scalar(select(Kpi).where(Kpi.name == kpi_name))
    if kpi is None:
        raise NotFoundError(f"KPI not found: {kpi_name}")
    return kpi


def _fetch_company_kpis(session: Session, company_id: int) -> list[Kpi]:
    """The KPIs a company reports, distinct, ordered by name."""
    query = (
        select(Kpi)
        .join(Estimate, Estimate.kpi_id == Kpi.id)
        .where(Estimate.company_id == company_id)
        .distinct()
        .order_by(Kpi.name)
    )
    return list(session.scalars(query).all())


# ---------------------------------------------------------------------------
# Companies and KPIs
# ---------------------------------------------------------------------------


def list_companies(session: Session, search: str | None = None) -> list[CompanySummary]:
    """List companies, optionally filtered by a case-insensitive search.

    The search matches the ticker, the company name, or the sector, so a single
    box finds a company whichever of the three the user typed.
    """
    query = select(Company)
    if search:
        term = f"%{search.strip()}%"
        query = query.where(
            Company.ticker.ilike(term) | Company.name.ilike(term) | Company.sector.ilike(term)
        )
    query = query.order_by(Company.ticker)
    return [CompanySummary.model_validate(c) for c in session.scalars(query).all()]


def get_company(session: Session, ticker: str) -> CompanyDetail:
    """Return one company and the KPIs it reports. Raises NotFoundError if unknown."""
    company = _get_company(session, ticker)
    kpis = _fetch_company_kpis(session, company.id)
    return CompanyDetail(
        ticker=company.ticker,
        name=company.name,
        sector=company.sector,
        kpis=[KpiInfo.model_validate(k) for k in kpis],
    )


def list_kpis(session: Session) -> list[KpiInfo]:
    """List every KPI name and its unit."""
    kpis = session.scalars(select(Kpi).order_by(Kpi.name)).all()
    return [KpiInfo.model_validate(k) for k in kpis]


# ---------------------------------------------------------------------------
# Series assembly (the QTD core)
# ---------------------------------------------------------------------------


def _fetch_history(
    session: Session,
    company_id: int,
    kpi_id: int,
    date_from: date | None,
    date_to: date | None,
) -> list[EstimatePoint]:
    """Historical estimates for one series, oldest first.

    The date range filters by `period_end`, the date the chart plots a
    historical point at. Both bounds are inclusive.
    """
    query = select(Estimate).where(
        Estimate.company_id == company_id,
        Estimate.kpi_id == kpi_id,
        Estimate.estimate_type == "historical",
    )
    if date_from is not None:
        query = query.where(Estimate.period_end >= date_from)
    if date_to is not None:
        query = query.where(Estimate.period_end <= date_to)
    query = query.order_by(Estimate.period_start)
    return [
        EstimatePoint(
            period=r.period,
            period_start=r.period_start,
            period_end=r.period_end,
            value=r.value,
            created_at=r.created_at,
        )
        for r in session.scalars(query).all()
    ]


def _fetch_qtd_snapshots(
    session: Session,
    company_id: int,
    kpi_id: int,
    date_from: date | None,
    date_to: date | None,
) -> list[QtdSnapshot]:
    """QTD snapshots for one series, one row per as_of, oldest first.

    DISTINCT ON (as_of) collapses re-published corrections at the same as_of to
    a single row. The order_by puts the winning row first within each as_of
    group: latest `created_at`, then highest `id` as the guaranteed-unique
    tiebreak (id is a BIGSERIAL, so a later insert always has a higher id, even
    when two rows written in one transaction share a created_at).

    The date range filters by `as_of`, the date the chart plots a QTD snapshot
    at. Both bounds are inclusive.
    """
    query = select(Estimate).where(
        Estimate.company_id == company_id,
        Estimate.kpi_id == kpi_id,
        Estimate.estimate_type == "qtd",
    )
    if date_from is not None:
        query = query.where(Estimate.as_of >= date_from)
    if date_to is not None:
        query = query.where(Estimate.as_of <= date_to)
    query = query.distinct(Estimate.as_of).order_by(
        Estimate.as_of, Estimate.created_at.desc(), Estimate.id.desc()
    )
    return [
        QtdSnapshot(
            period=r.period,
            period_start=r.period_start,
            period_end=r.period_end,
            value=r.value,
            as_of=r.as_of,
            created_at=r.created_at,
        )
        for r in session.scalars(query).all()
    ]


def _latest_created_at(
    history: list[EstimatePoint], qtd_snapshots: list[QtdSnapshot]
) -> datetime | None:
    """The most recent created_at across a series: the audit "last updated" time."""
    timestamps = [p.created_at for p in history]
    timestamps += [s.created_at for s in qtd_snapshots]
    return max(timestamps) if timestamps else None


def _assemble_series(
    session: Session,
    company: Company,
    kpi: Kpi,
    date_from: date | None,
    date_to: date | None,
) -> SeriesDetail:
    """Build a SeriesDetail from already-resolved company and KPI rows.

    Shared by get_series and get_company_estimates so the assembly logic is
    written once. `current_qtd` is the latest QTD snapshot in the (possibly
    filtered) view; the snapshots come back sorted by as_of, so it is the last.
    """
    history = _fetch_history(session, company.id, kpi.id, date_from, date_to)
    qtd_snapshots = _fetch_qtd_snapshots(session, company.id, kpi.id, date_from, date_to)
    current_qtd = qtd_snapshots[-1] if qtd_snapshots else None
    return SeriesDetail(
        ticker=company.ticker,
        company_name=company.name,
        kpi=kpi.name,
        unit=kpi.unit,
        history=history,
        qtd_snapshots=qtd_snapshots,
        current_qtd=current_qtd,
        last_updated=_latest_created_at(history, qtd_snapshots),
    )


def get_series(
    session: Session,
    ticker: str,
    kpi_name: str,
    date_from: date | None = None,
    date_to: date | None = None,
) -> SeriesDetail:
    """Return the full history and QTD snapshots for one (company, KPI) series.

    This is the drill-down query behind the detailed history-vs-QTD chart.
    Raises NotFoundError if the ticker or the KPI does not exist.
    """
    company = _get_company(session, ticker)
    kpi = _get_kpi(session, kpi_name)
    return _assemble_series(session, company, kpi, date_from, date_to)


def get_company_estimates(
    session: Session,
    ticker: str,
    date_from: date | None = None,
    date_to: date | None = None,
) -> CompanyEstimates:
    """Return every KPI series for one company.

    This is the "return all KPI estimates for a given company" endpoint. It
    resolves the company once, then assembles one SeriesDetail per KPI it
    reports. Raises NotFoundError for an unknown ticker.
    """
    company = _get_company(session, ticker)
    kpis = _fetch_company_kpis(session, company.id)
    series = [_assemble_series(session, company, kpi, date_from, date_to) for kpi in kpis]
    return CompanyEstimates(
        ticker=company.ticker,
        company_name=company.name,
        sector=company.sector,
        series=series,
    )


# ---------------------------------------------------------------------------
# Overview (the glanceable summary)
# ---------------------------------------------------------------------------


def _fetch_latest_historical(session: Session, search: str | None) -> list[Row]:
    """The newest historical estimate per series, with company and KPI metadata.

    DISTINCT ON (company_id, kpi_id) with period_end descending takes the most
    recent closed quarter for each series in one indexed pass. The optional
    search filters by ticker, company name, sector, or KPI name.
    """
    query = (
        select(
            Estimate.company_id,
            Estimate.kpi_id,
            Estimate.period,
            Estimate.value,
            Company.ticker,
            Company.name.label("company_name"),
            Company.sector,
            Kpi.name.label("kpi_name"),
            Kpi.unit,
        )
        .join(Company, Company.id == Estimate.company_id)
        .join(Kpi, Kpi.id == Estimate.kpi_id)
        .where(Estimate.estimate_type == "historical")
    )
    if search:
        term = f"%{search.strip()}%"
        query = query.where(
            Company.ticker.ilike(term)
            | Company.name.ilike(term)
            | Company.sector.ilike(term)
            | Kpi.name.ilike(term)
        )
    query = query.distinct(Estimate.company_id, Estimate.kpi_id).order_by(
        Estimate.company_id, Estimate.kpi_id, Estimate.period_end.desc()
    )
    return list(session.execute(query).all())


def _fetch_current_qtd_by_series(session: Session) -> dict[tuple[int, int], Estimate]:
    """The current QTD estimate per series, keyed by (company_id, kpi_id).

    DISTINCT ON (company_id, kpi_id) with as_of, created_at, id all descending
    takes the latest snapshot per series, resolving same-as_of corrections by
    the created_at then id tiebreak.
    """
    query = (
        select(Estimate)
        .where(Estimate.estimate_type == "qtd")
        .distinct(Estimate.company_id, Estimate.kpi_id)
        .order_by(
            Estimate.company_id,
            Estimate.kpi_id,
            Estimate.as_of.desc(),
            Estimate.created_at.desc(),
            Estimate.id.desc(),
        )
    )
    return {(r.company_id, r.kpi_id): r for r in session.scalars(query).all()}


def _fetch_sparklines(session: Session) -> dict[tuple[int, int], list[float]]:
    """The recent historical values per series, for the overview sparklines.

    One query fetches all historical values oldest first; Python groups them by
    series and keeps the most recent few of each.
    """
    query = (
        select(Estimate.company_id, Estimate.kpi_id, Estimate.value)
        .where(Estimate.estimate_type == "historical")
        .order_by(Estimate.company_id, Estimate.kpi_id, Estimate.period_start)
    )
    grouped: dict[tuple[int, int], list[float]] = defaultdict(list)
    for company_id, kpi_id, value in session.execute(query):
        grouped[(company_id, kpi_id)].append(float(value))
    return {key: values[-_SPARKLINE_POINTS:] for key, values in grouped.items()}


def get_overview(session: Session, search: str | None = None) -> OverviewResponse:
    """Return one glanceable card per (company, KPI) series.

    Each card carries the latest closed-quarter value, the current QTD value
    and its as_of, and a short sparkline of recent history. The optional search
    filters the cards by ticker, company name, sector, or KPI name.

    This runs a constant three queries regardless of how many series exist: the
    latest historical estimate per series, the current QTD per series, and the
    historical values feeding the sparklines. There is no per-series query, so
    no N+1. The three result sets are joined in Python on (company_id, kpi_id).
    """
    latest_historical = _fetch_latest_historical(session, search)
    current_qtd = _fetch_current_qtd_by_series(session)
    sparklines = _fetch_sparklines(session)

    cards: list[OverviewCard] = []
    for row in latest_historical:
        key = (row.company_id, row.kpi_id)
        qtd = current_qtd.get(key)
        cards.append(
            OverviewCard(
                ticker=row.ticker,
                company_name=row.company_name,
                sector=row.sector,
                kpi=row.kpi_name,
                unit=row.unit,
                latest_historical_value=row.value,
                latest_historical_period=row.period,
                current_qtd_value=qtd.value if qtd is not None else None,
                current_qtd_as_of=qtd.as_of if qtd is not None else None,
                sparkline=sparklines.get(key, []),
            )
        )
    cards.sort(key=lambda c: (c.ticker, c.kpi))
    return OverviewResponse(cards=cards)


# ---------------------------------------------------------------------------
# Publish (the only write)
# ---------------------------------------------------------------------------


def publish_estimate(session: Session, payload: PublishEstimateRequest) -> EstimateRecord:
    """Append one new estimate and return it.

    Publishing is append-only: it inserts a row, it never updates or deletes
    one. The full history of every estimate, including same-as_of corrections,
    is preserved as an audit trail. The Pydantic request schema has already
    validated every field, so this function only checks that the ticker and the
    KPI exist, then inserts.

    It flushes but does not commit: the caller owns the transaction.
    """
    company = _get_company(session, payload.ticker)
    kpi = _get_kpi(session, payload.kpi)

    estimate = Estimate(
        company_id=company.id,
        kpi_id=kpi.id,
        period=payload.period,
        period_start=payload.period_start,
        period_end=payload.period_end,
        estimate_type=payload.estimate_type,
        value=payload.value,
        as_of=payload.as_of,
    )
    session.add(estimate)
    # flush sends the INSERT now; refresh then loads the server-assigned id and
    # created_at (created_at comes from a server-side default).
    session.flush()
    session.refresh(estimate)

    logger.info(
        "estimate published: id=%s ticker=%s kpi=%s period=%s type=%s",
        estimate.id,
        company.ticker,
        kpi.name,
        estimate.period,
        estimate.estimate_type,
    )
    return EstimateRecord(
        id=estimate.id,
        ticker=company.ticker,
        kpi=kpi.name,
        period=estimate.period,
        period_start=estimate.period_start,
        period_end=estimate.period_end,
        estimate_type=estimate.estimate_type,
        value=estimate.value,
        as_of=estimate.as_of,
        created_at=estimate.created_at,
    )
