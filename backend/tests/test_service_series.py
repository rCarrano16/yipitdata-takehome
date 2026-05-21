"""Series assembly: history ordering, metadata, and date-range filtering.

The date range filters each point by the date the chart plots it at: historical
points by period_end, QTD snapshots by as_of. Both bounds are inclusive.
"""

from datetime import date

from app.service import get_series


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
