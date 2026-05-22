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

from sqlalchemy import ColumnElement, Row, func, select
from sqlalchemy.orm import Session

from app.analytics import compute_analytics
from app.errors import NotFoundError
from app.models import Company, Estimate, Kpi
from app.schemas import (
    CompanyDetail,
    CompanyEstimates,
    CompanySummary,
    EstimatePoint,
    EstimateRecord,
    KpiComparison,
    KpiComparisonRow,
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
    """Return the KPI for a name, or raise NotFoundError. Case-insensitive."""
    kpi = session.scalar(select(Kpi).where(func.lower(Kpi.name) == kpi_name.lower()))
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
    """Historical estimates for one series, one row per closed quarter, oldest first.

    DISTINCT ON (period) collapses a re-published historical correction for the
    same closed quarter to a single row, mirroring the QTD snapshot dedup: the
    winning row is the latest `created_at`, then the highest `id` as the
    guaranteed-unique tiebreak. DISTINCT ON requires `period` to lead the
    ORDER BY, so the points are sorted afterwards by `period_end`, the date the
    chart plots a historical point at and the column the date range filters on.
    Both date bounds are inclusive.
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
    query = query.distinct(Estimate.period).order_by(
        Estimate.period, Estimate.created_at.desc(), Estimate.id.desc()
    )
    points = [
        EstimatePoint(
            period=r.period,
            period_start=r.period_start,
            period_end=r.period_end,
            value=r.value,
            created_at=r.created_at,
        )
        for r in session.scalars(query).all()
    ]
    points.sort(key=lambda p: p.period_end)
    return points


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
    written once.

    `history` and `qtd_snapshots` are the plotted arrays: they answer to the
    date filter, so they hold exactly the points the chart draws. `current_qtd`,
    `last_updated`, and `analytics` are series-level summary fields: they
    describe the whole series and are always computed from the full, unfiltered
    data, so narrowing the chart's date range never changes them. An unfiltered
    request already holds the full data; a filtered one fetches it once more, so
    the summary fields cost one extra history query and one extra QTD query.
    """
    history = _fetch_history(session, company.id, kpi.id, date_from, date_to)
    qtd_snapshots = _fetch_qtd_snapshots(session, company.id, kpi.id, date_from, date_to)
    if date_from is None and date_to is None:
        full_history = history
        full_qtd = qtd_snapshots
    else:
        full_history = _fetch_history(session, company.id, kpi.id, None, None)
        full_qtd = _fetch_qtd_snapshots(session, company.id, kpi.id, None, None)
    return SeriesDetail(
        ticker=company.ticker,
        company_name=company.name,
        kpi=kpi.name,
        unit=kpi.unit,
        history=history,
        qtd_snapshots=qtd_snapshots,
        current_qtd=full_qtd[-1] if full_qtd else None,
        last_updated=_latest_created_at(full_history, full_qtd),
        analytics=compute_analytics(full_history),
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
    # One _assemble_series call per KPI, so this is 2N+2 indexed queries (N is
    # the KPI count, at most 5 in this dataset). Left per-series for readability:
    # a batched two-query form is the optimization if a company ever reports
    # many KPIs, but it buys nothing measurable at this scale.
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


def _overview_search_predicate(search: str) -> ColumnElement[bool]:
    """The overview search filter: a case-insensitive match on ticker, company
    name, sector, or KPI name.

    Returns a SQLAlchemy boolean expression for a query already joined to
    Company and Kpi. All three overview fetches use it, so they always match on
    the same four columns and a filtered overview narrows every fetch alike.
    """
    term = f"%{search.strip()}%"
    return (
        Company.ticker.ilike(term)
        | Company.name.ilike(term)
        | Company.sector.ilike(term)
        | Kpi.name.ilike(term)
    )


def _fetch_latest_historical(session: Session, search: str | None) -> list[Row]:
    """The newest historical estimate per series, with company and KPI metadata.

    DISTINCT ON (company_id, kpi_id) takes one row per series in a single
    indexed pass. The ORDER BY decides which row: the latest `period_end` (the
    most recent closed quarter), then `created_at` then `id` descending to break
    a tie when a correction has been re-published for that same quarter. The
    optional search filters by ticker, company name, sector, or KPI name.
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
        query = query.where(_overview_search_predicate(search))
    query = query.distinct(Estimate.company_id, Estimate.kpi_id).order_by(
        Estimate.company_id,
        Estimate.kpi_id,
        Estimate.period_end.desc(),
        Estimate.created_at.desc(),
        Estimate.id.desc(),
    )
    return list(session.execute(query).all())


def _fetch_current_qtd_by_series(
    session: Session, search: str | None = None
) -> dict[tuple[int, int], Estimate]:
    """The current QTD estimate per series, keyed by (company_id, kpi_id).

    DISTINCT ON (company_id, kpi_id) with as_of, created_at, id all descending
    takes the latest snapshot per series, resolving same-as_of corrections by
    the created_at then id tiebreak. The optional search narrows the result to
    the matching series, so a filtered overview does not fetch every series.
    """
    query = select(Estimate).where(Estimate.estimate_type == "qtd")
    if search:
        query = (
            query.join(Company, Company.id == Estimate.company_id)
            .join(Kpi, Kpi.id == Estimate.kpi_id)
            .where(_overview_search_predicate(search))
        )
    query = query.distinct(Estimate.company_id, Estimate.kpi_id).order_by(
        Estimate.company_id,
        Estimate.kpi_id,
        Estimate.as_of.desc(),
        Estimate.created_at.desc(),
        Estimate.id.desc(),
    )
    return {(r.company_id, r.kpi_id): r for r in session.scalars(query).all()}


def _fetch_sparklines(
    session: Session, search: str | None = None
) -> dict[tuple[int, int], list[float]]:
    """The recent historical values per series, for the overview sparklines.

    DISTINCT ON (company_id, kpi_id, period) collapses a re-published historical
    correction to one row per quarter, the latest created_at then highest id
    winning, exactly as _fetch_history does for the detail chart. Python then
    groups the rows by series, sorts each group by period_end, and keeps the
    most recent few values. The optional search narrows the query to the
    matching series, so a filtered overview does not fetch every series' history.
    """
    query = select(
        Estimate.company_id,
        Estimate.kpi_id,
        Estimate.period,
        Estimate.period_end,
        Estimate.value,
    ).where(Estimate.estimate_type == "historical")
    if search:
        query = (
            query.join(Company, Company.id == Estimate.company_id)
            .join(Kpi, Kpi.id == Estimate.kpi_id)
            .where(_overview_search_predicate(search))
        )
    query = query.distinct(Estimate.company_id, Estimate.kpi_id, Estimate.period).order_by(
        Estimate.company_id,
        Estimate.kpi_id,
        Estimate.period,
        Estimate.created_at.desc(),
        Estimate.id.desc(),
    )
    grouped: dict[tuple[int, int], list[tuple[date, float]]] = defaultdict(list)
    for company_id, kpi_id, _period, period_end, value in session.execute(query):
        grouped[(company_id, kpi_id)].append((period_end, float(value)))
    sparklines: dict[tuple[int, int], list[float]] = {}
    for key, points in grouped.items():
        points.sort(key=lambda point: point[0])
        sparklines[key] = [value for _period_end, value in points[-_SPARKLINE_POINTS:]]
    return sparklines


def get_overview(session: Session, search: str | None = None) -> OverviewResponse:
    """Return one glanceable card per (company, KPI) series.

    Each card carries the latest closed-quarter value, the current QTD value
    and its as_of, and a short sparkline of recent history. The optional search
    filters the cards by ticker, company name, sector, or KPI name.

    This runs a constant three queries regardless of how many series exist: the
    latest historical estimate per series, the current QTD per series, and the
    historical values feeding the sparklines. There is no per-series query, so
    no N+1. When a search is given it is applied to all three queries, so a
    filtered overview fetches only the series it will show. The three result
    sets are joined in Python on (company_id, kpi_id).
    """
    latest_historical = _fetch_latest_historical(session, search)
    current_qtd = _fetch_current_qtd_by_series(session, search)
    sparklines = _fetch_sparklines(session, search)

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
# Comparison (one KPI across companies)
# ---------------------------------------------------------------------------


def _resolve_comparison_companies(
    session: Session, kpi: Kpi, tickers: list[str] | None
) -> list[Company]:
    """Resolve the companies a KPI comparison covers.

    With no tickers, every company that reports the KPI. With an explicit list,
    exactly those companies, resolved case-insensitively; an unknown ticker
    raises NotFoundError, so a typo fails loudly instead of silently dropping a
    column from the comparison.
    """
    if not tickers:
        query = (
            select(Company)
            .join(Estimate, Estimate.company_id == Company.id)
            .where(Estimate.kpi_id == kpi.id)
            .distinct()
            .order_by(Company.ticker)
        )
        return list(session.scalars(query).all())
    found = {
        c.ticker.lower(): c
        for c in session.scalars(
            select(Company).where(
                func.lower(Company.ticker).in_([t.strip().lower() for t in tickers])
            )
        ).all()
    }
    companies: list[Company] = []
    for ticker in tickers:
        company = found.get(ticker.strip().lower())
        if company is None:
            raise NotFoundError(f"company not found: {ticker}")
        companies.append(company)
    return companies


def _fetch_kpi_history_by_company(
    session: Session, kpi_id: int, company_ids: list[int]
) -> dict[int, list[EstimatePoint]]:
    """Closed-quarter history for one KPI across many companies, in one query.

    The batched form of _fetch_history. DISTINCT ON (company_id, period)
    collapses a re-published correction to one row per quarter, the latest
    created_at then highest id winning. The rows are grouped by company in
    Python and each group sorted by period_end, so there is one query for every
    company, never one query each.
    """
    if not company_ids:
        return {}
    query = (
        select(Estimate)
        .where(
            Estimate.kpi_id == kpi_id,
            Estimate.estimate_type == "historical",
            Estimate.company_id.in_(company_ids),
        )
        .distinct(Estimate.company_id, Estimate.period)
        .order_by(
            Estimate.company_id,
            Estimate.period,
            Estimate.created_at.desc(),
            Estimate.id.desc(),
        )
    )
    grouped: dict[int, list[EstimatePoint]] = defaultdict(list)
    for r in session.scalars(query).all():
        grouped[r.company_id].append(
            EstimatePoint(
                period=r.period,
                period_start=r.period_start,
                period_end=r.period_end,
                value=r.value,
                created_at=r.created_at,
            )
        )
    for points in grouped.values():
        points.sort(key=lambda p: p.period_end)
    return dict(grouped)


def _fetch_kpi_current_qtd_by_company(
    session: Session, kpi_id: int, company_ids: list[int]
) -> dict[int, QtdSnapshot]:
    """The current QTD snapshot for one KPI per company, in one query.

    DISTINCT ON (company_id) with as_of, created_at, id all descending takes the
    latest snapshot per company, the same resolution _fetch_current_qtd_by_series
    uses, narrowed to a single KPI.
    """
    if not company_ids:
        return {}
    query = (
        select(Estimate)
        .where(
            Estimate.kpi_id == kpi_id,
            Estimate.estimate_type == "qtd",
            Estimate.company_id.in_(company_ids),
        )
        .distinct(Estimate.company_id)
        .order_by(
            Estimate.company_id,
            Estimate.as_of.desc(),
            Estimate.created_at.desc(),
            Estimate.id.desc(),
        )
    )
    return {
        r.company_id: QtdSnapshot(
            period=r.period,
            period_start=r.period_start,
            period_end=r.period_end,
            value=r.value,
            as_of=r.as_of,
            created_at=r.created_at,
        )
        for r in session.scalars(query).all()
    }


def compare_kpi(
    session: Session,
    kpi_name: str,
    tickers: list[str] | None = None,
) -> KpiComparison:
    """Compare one KPI across several companies, one row each.

    For the KPI, returns each company's latest closed-quarter value, its current
    QTD value, and its YoY/QoQ trend signals, so an agent can rank peers on a
    single metric. With no tickers it covers every company reporting the KPI.

    Runs a constant four queries regardless of company count: resolve the KPI,
    resolve the companies, then one batched history query and one batched QTD
    query. There is no per-company query, so no N+1. Raises NotFoundError for an
    unknown KPI or an unknown ticker.
    """
    kpi = _get_kpi(session, kpi_name)
    companies = _resolve_comparison_companies(session, kpi, tickers)
    company_ids = [c.id for c in companies]
    history_by_company = _fetch_kpi_history_by_company(session, kpi.id, company_ids)
    qtd_by_company = _fetch_kpi_current_qtd_by_company(session, kpi.id, company_ids)

    rows: list[KpiComparisonRow] = []
    for company in companies:
        history = history_by_company.get(company.id, [])
        latest = history[-1] if history else None
        qtd = qtd_by_company.get(company.id)
        rows.append(
            KpiComparisonRow(
                ticker=company.ticker,
                company_name=company.name,
                sector=company.sector,
                latest_historical_value=latest.value if latest is not None else None,
                latest_historical_period=latest.period if latest is not None else None,
                current_qtd_value=qtd.value if qtd is not None else None,
                current_qtd_as_of=qtd.as_of if qtd is not None else None,
                analytics=compute_analytics(history),
            )
        )
    rows.sort(key=lambda r: r.ticker)
    return KpiComparison(kpi=kpi.name, unit=kpi.unit, companies=rows)


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
