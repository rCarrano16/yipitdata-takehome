"""Closed-quarter analytics: YoY and QoQ percent changes from a pure history.

compute_analytics is a pure function, so these tests build EstimatePoint lists
by hand and need no database. They cover the normal YoY/QoQ case, the year
boundary, a missing comparison quarter, a gap in the history, a zero base, an
empty history, a negative move, and a malformed period code.
"""

from datetime import date, datetime

from app.analytics import compute_analytics
from app.schemas import EstimatePoint

# compute_analytics only reads `period` and `value`; created_at is a placeholder.
_CREATED = datetime(2026, 1, 1, 12, 0, 0)


def _point(period: str, value: float) -> EstimatePoint:
    """A historical point for one quarter, with placeholder date fields.

    The period_start / period_end are derived from the quarter code so the
    EstimatePoint validates, but compute_analytics never reads them.
    """
    year = int(period[:4])
    quarter = int(period[5])
    start_month = (quarter - 1) * 3 + 1
    return EstimatePoint(
        period=period,
        period_start=date(year, start_month, 1),
        period_end=date(year, start_month + 2, 28),
        value=value,
        created_at=_CREATED,
    )


def test_qoq_is_the_change_from_the_previous_quarter():
    analytics = compute_analytics([_point("2025Q3", 100.0), _point("2025Q4", 110.0)])
    assert analytics.latest_period == "2025Q4"
    assert analytics.qoq == (110.0 - 100.0) / 100.0


def test_yoy_is_the_change_from_the_same_quarter_last_year():
    history = [
        _point("2024Q4", 80.0),
        _point("2025Q1", 90.0),
        _point("2025Q2", 95.0),
        _point("2025Q3", 100.0),
        _point("2025Q4", 120.0),
    ]
    analytics = compute_analytics(history)
    assert analytics.yoy == (120.0 - 80.0) / 80.0
    assert analytics.qoq == (120.0 - 100.0) / 100.0


def test_yoy_crosses_the_year_boundary():
    # 2025Q1's year-ago quarter is 2024Q1, and its previous quarter is 2024Q4:
    # both comparisons must step the quarter ordinal across the year boundary.
    history = [_point("2024Q1", 50.0), _point("2024Q4", 70.0), _point("2025Q1", 60.0)]
    analytics = compute_analytics(history)
    assert analytics.latest_period == "2025Q1"
    assert analytics.yoy == (60.0 - 50.0) / 50.0
    assert analytics.qoq == (60.0 - 70.0) / 70.0


def test_missing_comparison_quarter_yields_none():
    # A single quarter has no previous quarter and no year-ago quarter.
    analytics = compute_analytics([_point("2025Q4", 120.0)])
    assert analytics.latest_period == "2025Q4"
    assert analytics.qoq is None
    assert analytics.yoy is None


def test_a_gap_before_the_latest_quarter_yields_no_qoq():
    # 2025Q2 then 2025Q4: the immediately preceding quarter 2025Q3 is absent,
    # so QoQ is None rather than a misleading comparison across the gap.
    analytics = compute_analytics([_point("2025Q2", 100.0), _point("2025Q4", 120.0)])
    assert analytics.qoq is None


def test_zero_base_yields_none_not_division_by_zero():
    analytics = compute_analytics([_point("2025Q3", 0.0), _point("2025Q4", 10.0)])
    assert analytics.qoq is None


def test_a_negative_move_is_reported_as_a_negative_change():
    analytics = compute_analytics([_point("2025Q3", 100.0), _point("2025Q4", 75.0)])
    assert analytics.qoq == (75.0 - 100.0) / 100.0
    assert analytics.qoq < 0


def test_empty_history_yields_all_none():
    analytics = compute_analytics([])
    assert analytics.latest_period is None
    assert analytics.qoq is None
    assert analytics.yoy is None


def test_a_malformed_period_is_ignored():
    # _period_ordinal returns None for a code it cannot parse, so a stray
    # malformed row is skipped and never becomes the latest quarter.
    bad = EstimatePoint(
        period="garbage",
        period_start=date(2025, 1, 1),
        period_end=date(2025, 3, 31),
        value=999.0,
        created_at=_CREATED,
    )
    analytics = compute_analytics([bad, _point("2025Q4", 120.0)])
    assert analytics.latest_period == "2025Q4"
