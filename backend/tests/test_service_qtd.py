"""QTD resolution: current QTD is the latest as_of, with a deterministic tiebreak.

This is the heart of the assignment. A QTD estimate is not one value, it is a
series of intra-quarter snapshots; the current value is the snapshot with the
latest as_of, and a same-as_of correction must resolve deterministically.
"""

from datetime import date
from decimal import Decimal

from app.schemas import PublishEstimateRequest
from app.service import get_series, publish_estimate


def test_current_qtd_is_the_latest_as_of(db_session):
    series = get_series(db_session, "ACME", "Total Revenue ($MM)")
    assert series.current_qtd is not None
    assert series.current_qtd.as_of == date(2026, 3, 15)
    assert series.current_qtd.value == 40.0


def test_qtd_snapshots_resolve_in_as_of_order_despite_insertion_order(db_session):
    # The fixture inserts ACME's QTD rows out of as_of order on purpose.
    series = get_series(db_session, "ACME", "Total Revenue ($MM)")
    as_ofs = [s.as_of for s in series.qtd_snapshots]
    assert as_ofs == [date(2026, 1, 31), date(2026, 2, 15), date(2026, 3, 15)]


def test_series_without_qtd_has_no_current_qtd(db_session):
    series = get_series(db_session, "ACME", "Units Sold")
    assert series.qtd_snapshots == []
    assert series.current_qtd is None


def test_publishing_a_newer_as_of_becomes_current_qtd(db_session):
    request = PublishEstimateRequest(
        ticker="ACME",
        kpi="Total Revenue ($MM)",
        period="2026Q1",
        period_start=date(2026, 1, 1),
        period_end=date(2026, 3, 31),
        estimate_type="qtd",
        value=Decimal("45"),
        as_of=date(2026, 3, 31),
    )
    publish_estimate(db_session, request)

    series = get_series(db_session, "ACME", "Total Revenue ($MM)")
    assert series.current_qtd is not None
    assert series.current_qtd.as_of == date(2026, 3, 31)
    assert series.current_qtd.value == 45.0


def test_same_as_of_correction_resolves_to_the_newest_row(db_session):
    """Two QTD rows at one as_of: the most recently inserted (higher id) wins.

    Both rows are inserted in this one test transaction, so func.now() gives
    them an identical created_at. Only the id DESC tiebreak distinguishes them,
    which is exactly the case this test pins down: the corrected value 55, not
    the original 50, must surface.
    """
    base = dict(
        ticker="ACME",
        kpi="Total Revenue ($MM)",
        period="2026Q1",
        period_start=date(2026, 1, 1),
        period_end=date(2026, 3, 31),
        estimate_type="qtd",
        as_of=date(2026, 2, 28),
    )
    publish_estimate(db_session, PublishEstimateRequest(**base, value=Decimal("50")))
    publish_estimate(db_session, PublishEstimateRequest(**base, value=Decimal("55")))

    series = get_series(db_session, "ACME", "Total Revenue ($MM)")
    snapshot = next(s for s in series.qtd_snapshots if s.as_of == date(2026, 2, 28))
    assert snapshot.value == 55.0
