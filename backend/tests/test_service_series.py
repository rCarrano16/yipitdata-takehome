"""Series assembly: history ordering, metadata, and date-range filtering.

The date range filters each point by the date the chart plots it at: historical
points by period_end, QTD snapshots by as_of. Both bounds are inclusive.
"""

from datetime import date
from decimal import Decimal

from app.schemas import PublishEstimateRequest
from app.service import get_series, publish_estimate


def test_history_is_ordered_oldest_first(db_session):
    series = get_series(db_session, "ACME", "Total Revenue ($MM)")
    periods = [p.period for p in series.history]
    assert periods == ["2025Q2", "2025Q3", "2025Q4"]


def test_series_carries_company_name_and_kpi_unit(db_session):
    series = get_series(db_session, "ACME", "Total Revenue ($MM)")
    assert series.company_name == "Acme Cloud Inc"
    assert series.kpi == "Total Revenue ($MM)"
    assert series.unit == "$MM"


def test_last_updated_is_the_newest_created_at(db_session):
    series = get_series(db_session, "ACME", "Total Revenue ($MM)")
    newest = max(
        [p.created_at for p in series.history] + [s.created_at for s in series.qtd_snapshots]
    )
    assert series.last_updated == newest


def test_date_filter_keeps_historical_by_period_end_inclusive(db_session):
    # 2025Q2 ends 2025-06-30, 2025Q3 ends 2025-09-30, 2025Q4 ends 2025-12-31.
    series = get_series(
        db_session,
        "ACME",
        "Total Revenue ($MM)",
        date_from=date(2025, 9, 30),
        date_to=date(2025, 12, 31),
    )
    periods = [p.period for p in series.history]
    # The 2025-09-30 lower bound is inclusive, so 2025Q3 stays in.
    assert periods == ["2025Q3", "2025Q4"]


def test_date_filter_keeps_qtd_by_as_of_inclusive(db_session):
    # QTD as_of dates: 2026-01-31, 2026-02-15, 2026-03-15.
    series = get_series(
        db_session,
        "ACME",
        "Total Revenue ($MM)",
        date_from=date(2026, 1, 31),
        date_to=date(2026, 2, 15),
    )
    as_ofs = [s.as_of for s in series.qtd_snapshots]
    # Both bounds are inclusive.
    assert as_ofs == [date(2026, 1, 31), date(2026, 2, 15)]
    # current_qtd is the latest as_of within the filtered view.
    assert series.current_qtd is not None
    assert series.current_qtd.as_of == date(2026, 2, 15)


def test_date_filter_can_exclude_every_point(db_session):
    series = get_series(
        db_session,
        "ACME",
        "Total Revenue ($MM)",
        date_from=date(2020, 1, 1),
        date_to=date(2020, 12, 31),
    )
    assert series.history == []
    assert series.qtd_snapshots == []
    assert series.current_qtd is None
    assert series.last_updated is None


def test_kpi_lookup_is_case_insensitive(db_session):
    # The KPI lookup matches case-insensitively, like the company lookup, so an
    # LLM (or a user) need not reproduce the exact casing of "Total Revenue ($MM)".
    series = get_series(db_session, "ACME", "total revenue ($mm)")
    assert series.kpi == "Total Revenue ($MM)"


def test_same_period_historical_correction_resolves_to_the_newest_row(db_session):
    """Two historical rows for one closed quarter: the newest (higher id) wins.

    Publishing is append-only for historical estimates too, so a re-published
    correction is a second row for the same period. _fetch_history deduplicates
    with DISTINCT ON (period), mirroring the QTD snapshot dedup, so the series
    shows one point per quarter and the corrected value is the one that surfaces.
    Both rows are written in this one transaction, so func.now() ties their
    created_at; only the id DESC tiebreak distinguishes them.
    """
    base = dict(
        ticker="ACME",
        kpi="Total Revenue ($MM)",
        period="2025Q4",
        period_start=date(2025, 10, 1),
        period_end=date(2025, 12, 31),
        estimate_type="historical",
        as_of=None,
    )
    publish_estimate(db_session, PublishEstimateRequest(**base, value=Decimal("130")))
    publish_estimate(db_session, PublishEstimateRequest(**base, value=Decimal("135")))

    series = get_series(db_session, "ACME", "Total Revenue ($MM)")
    periods = [p.period for p in series.history]
    # 2025Q4 still appears exactly once despite the correction.
    assert periods == ["2025Q2", "2025Q3", "2025Q4"]
    q4 = next(p for p in series.history if p.period == "2025Q4")
    assert q4.value == 135.0


def test_series_carries_analytics_from_the_history(db_session):
    # ACME / Total Revenue history: 2025Q2=100, 2025Q3=110, 2025Q4=120.
    series = get_series(db_session, "ACME", "Total Revenue ($MM)")
    assert series.analytics.latest_period == "2025Q4"
    # QoQ compares the latest closed quarter, 2025Q4, to 2025Q3.
    assert series.analytics.qoq == (120.0 - 110.0) / 110.0
    # The fixture has no 2024Q4, so YoY cannot be computed.
    assert series.analytics.yoy is None


def test_analytics_use_the_full_history_not_the_date_filtered_view(db_session):
    """Decision D1: a date filter narrows the chart but not the analytics.

    Filtering to just 2025Q4 leaves one point on the history line, but QoQ is
    still 2025Q4 vs 2025Q3, computed from the full unfiltered history, so the
    trend signal stays stable as the user narrows the chart.
    """
    series = get_series(
        db_session,
        "ACME",
        "Total Revenue ($MM)",
        date_from=date(2025, 10, 1),
        date_to=date(2025, 12, 31),
    )
    # The chart view is narrowed to the single in-range quarter.
    assert [p.period for p in series.history] == ["2025Q4"]
    # The analytics are unchanged: still computed from 2025Q2/Q3/Q4.
    assert series.analytics.latest_period == "2025Q4"
    assert series.analytics.qoq == (120.0 - 110.0) / 110.0
