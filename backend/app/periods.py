"""Quarter period codes: the canonical calendar window for a code like "2026Q1".

A period code names a fiscal quarter that is also a calendar quarter: Q1 is
January through March, Q2 April through June, Q3 July through September, Q4
October through December. The window is therefore fully determined by the code,
and no quarter ever ends in February, so `quarter_window` is a fixed lookup.

Both the publish request schema and the CSV seed use it to reject a row whose
period_start / period_end do not match the quarter its `period` code names.
"""

from datetime import date

# Each quarter's (start month, start day) and (end month, end day). Fixed for
# every year: no quarter boundary moves.
_QUARTER_WINDOWS: dict[int, tuple[tuple[int, int], tuple[int, int]]] = {
    1: ((1, 1), (3, 31)),
    2: ((4, 1), (6, 30)),
    3: ((7, 1), (9, 30)),
    4: ((10, 1), (12, 31)),
}


def quarter_window(period: str) -> tuple[date, date]:
    """Return the (period_start, period_end) the quarter code denotes.

    `period` must already be a validated quarter code: four digits, then "Q",
    then 1-4 (the format both the publish schema and the seed check first).
    """
    year = int(period[:4])
    quarter = int(period[5])
    (start_month, start_day), (end_month, end_day) = _QUARTER_WINDOWS[quarter]
    return date(year, start_month, start_day), date(year, end_month, end_day)
