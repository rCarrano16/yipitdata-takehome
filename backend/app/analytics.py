"""Closed-quarter trend analytics: pure functions over a KPI history.

These compute the year-over-year (YoY) and quarter-over-quarter (QoQ) percent
changes for a series. The functions are pure: a list of historical points goes
in, a SeriesAnalytics comes out, with no database and no I/O, so they are
trivial to test and produce identical results for both API consumers.

Only closed-quarter (historical) estimates feed these signals. A QTD estimate
is a partial, cumulative-to-date value, so comparing one quarter's QTD against
another's would mislead. A closed quarter is complete, so two closed quarters
are directly comparable for every KPI with no modeling assumption.
"""

import re

from app.schemas import EstimatePoint, SeriesAnalytics

# A period code is a quarter like "2025Q4": a four-digit year, "Q", quarter 1-4.
_PERIOD_PATTERN = re.compile(r"^(\d{4})Q([1-4])$")

# One year is four quarters. Used both to size the quarter ordinal and to step
# back to the same quarter of the previous year for the YoY comparison.
_QUARTERS_IN_YEAR = 4


def _period_ordinal(period: str) -> int | None:
    """Convert a quarter code like "2025Q4" into a sortable integer ordinal.

    The ordinal is year * 4 + (quarter - 1), so two consecutive quarters differ
    by exactly 1 and quarters one year apart differ by exactly 4. Returns None
    for a code that does not match the expected format.
    """
    match = _PERIOD_PATTERN.match(period)
    if match is None:
        return None
    year, quarter = int(match.group(1)), int(match.group(2))
    return year * _QUARTERS_IN_YEAR + (quarter - 1)


def _percent_change(latest: float, prior: float) -> float | None:
    """The fractional change from prior to latest: 0.05 means a +5% move.

    Returns None when prior is zero: a percent change off a zero base is
    undefined, and reporting one would be misleading.
    """
    if prior == 0:
        return None
    return (latest - prior) / prior


def compute_analytics(history: list[EstimatePoint]) -> SeriesAnalytics:
    """Compute the YoY and QoQ percent changes from a series' closed-quarter history.

    `history` must be the full, unfiltered list of historical points: the
    chart's date filter must not change these numbers. QoQ compares the latest
    closed quarter to the immediately preceding quarter; YoY compares it to the
    same quarter one year (four quarters) earlier. A signal is None when its
    comparison quarter is missing from the data or has a zero value, so the UI
    never shows a misleading number.
    """
    points_by_ordinal: dict[int, EstimatePoint] = {}
    for point in history:
        ordinal = _period_ordinal(point.period)
        if ordinal is not None:
            points_by_ordinal[ordinal] = point

    if not points_by_ordinal:
        return SeriesAnalytics(latest_period=None, qoq=None, yoy=None)

    latest_ordinal = max(points_by_ordinal)
    latest = points_by_ordinal[latest_ordinal]
    prior_quarter = points_by_ordinal.get(latest_ordinal - 1)
    year_ago = points_by_ordinal.get(latest_ordinal - _QUARTERS_IN_YEAR)

    qoq = None
    if prior_quarter is not None:
        qoq = _percent_change(latest.value, prior_quarter.value)

    yoy = None
    if year_ago is not None:
        yoy = _percent_change(latest.value, year_ago.value)

    return SeriesAnalytics(latest_period=latest.period, qoq=qoq, yoy=yoy)
