"""Company lookups, KPI listing, the overview, and the KPI comparison.

The overview and the comparison each carry a query-count test proving there is
no N+1.
"""

from datetime import date

import pytest

from app.errors import NotFoundError
from app.service import (
    _fetch_current_qtd_by_series,
    _fetch_sparklines,
    compare_kpi,
    get_company,
    get_overview,
    list_companies,
    list_kpis,
)


def test_list_companies_returns_all(db_session):
    companies = list_companies(db_session)
    assert {c.ticker for c in companies} == {"ACME", "BETA", "GAMM"}


def test_search_matches_sector_case_insensitively(db_session):
    results = list_companies(db_session, search="cloud")
    assert {c.ticker for c in results} == {"ACME", "GAMM"}


def test_search_matches_ticker(db_session):
    results = list_companies(db_session, search="beta")
    assert [c.ticker for c in results] == ["BETA"]


def test_search_matches_company_name(db_session):
    results = list_companies(db_session, search="acme cloud")
    assert [c.ticker for c in results] == ["ACME"]


def test_get_company_lists_its_kpis(db_session):
    company = get_company(db_session, "ACME")
    assert company.name == "Acme Cloud Inc"
    assert {k.name for k in company.kpis} == {"Total Revenue ($MM)", "Units Sold"}


def test_get_company_unknown_ticker_raises(db_session):
    with pytest.raises(NotFoundError):
        get_company(db_session, "NOPE")


def test_list_kpis_returns_names_and_units(db_session):
    kpis = list_kpis(db_session)
    assert {k.name: k.unit for k in kpis} == {
        "Total Revenue ($MM)": "$MM",
        "Units Sold": "units",
    }


def test_overview_has_one_card_per_series(db_session):
    overview = get_overview(db_session)
    keys = {(c.ticker, c.kpi) for c in overview.cards}
    assert keys == {
        ("ACME", "Total Revenue ($MM)"),
        ("ACME", "Units Sold"),
        ("GAMM", "Total Revenue ($MM)"),
        ("BETA", "Total Revenue ($MM)"),
    }


def test_overview_card_carries_latest_value_qtd_and_sparkline(db_session):
    overview = get_overview(db_session)
    card = next(c for c in overview.cards if c.ticker == "ACME" and c.kpi == "Total Revenue ($MM)")
    assert card.latest_historical_value == 120.0
    assert card.latest_historical_period == "2025Q4"
    assert card.current_qtd_value == 40.0
    assert card.current_qtd_as_of == date(2026, 3, 15)
    assert card.sparkline == [100.0, 110.0, 120.0]


def test_overview_card_without_qtd_has_null_qtd_fields(db_session):
    overview = get_overview(db_session)
    card = next(c for c in overview.cards if c.ticker == "ACME" and c.kpi == "Units Sold")
    assert card.current_qtd_value is None
    assert card.current_qtd_as_of is None


def test_overview_search_filters_cards(db_session):
    overview = get_overview(db_session, search="retail")
    assert {c.ticker for c in overview.cards} == {"BETA"}


def test_overview_search_keeps_qtd_and_sparkline_for_surviving_cards(db_session):
    """The narrowed QTD and sparkline fetches still resolve correctly: a card
    that survives the filter carries its current QTD and its sparkline."""
    overview = get_overview(db_session, search="retail")
    card = next(c for c in overview.cards if c.ticker == "BETA")
    assert card.current_qtd_value == 70.0
    assert card.current_qtd_as_of == date(2026, 3, 15)
    assert card.sparkline == [200.0, 210.0]


def test_overview_search_narrows_the_qtd_and_sparkline_fetches(db_session):
    """A filtered overview must not over-fetch.

    get_overview's output is identical whether or not the QTD and sparkline
    fetches honor the search (unmatched entries would simply go unused), so the
    narrowing is asserted directly on the two fetch helpers: with a search they
    return only the matching series, not every series.
    """
    assert len(_fetch_current_qtd_by_series(db_session)) == 2
    assert len(_fetch_current_qtd_by_series(db_session, search="retail")) == 1
    assert len(_fetch_sparklines(db_session)) == 4
    assert len(_fetch_sparklines(db_session, search="retail")) == 1


def test_overview_runs_a_constant_number_of_queries(db_session, query_counter):
    """get_overview must not issue a query per series (no N+1).

    Three queries: latest historical per series, current QTD per series, and the
    historical values for the sparklines. The count is fixed by the code, not by
    how many series the fixture holds.
    """
    query_counter.count = 0
    get_overview(db_session)
    assert query_counter.count == 3


def test_compare_kpi_returns_a_row_per_reporting_company(db_session):
    comparison = compare_kpi(db_session, "Total Revenue ($MM)")
    assert comparison.kpi == "Total Revenue ($MM)"
    assert comparison.unit == "$MM"
    # Sorted by ticker; all three companies report this KPI.
    assert [r.ticker for r in comparison.companies] == ["ACME", "BETA", "GAMM"]


def test_compare_kpi_row_carries_latest_value_qtd_and_analytics(db_session):
    comparison = compare_kpi(db_session, "Total Revenue ($MM)")
    acme = next(r for r in comparison.companies if r.ticker == "ACME")
    assert acme.latest_historical_value == 120.0
    assert acme.latest_historical_period == "2025Q4"
    assert acme.current_qtd_value == 40.0
    assert acme.current_qtd_as_of == date(2026, 3, 15)
    assert acme.analytics.latest_period == "2025Q4"
    assert acme.analytics.qoq == pytest.approx((120 - 110) / 110)


def test_compare_kpi_row_without_qtd_has_null_qtd_fields(db_session):
    comparison = compare_kpi(db_session, "Total Revenue ($MM)")
    gamm = next(r for r in comparison.companies if r.ticker == "GAMM")
    assert gamm.current_qtd_value is None
    assert gamm.current_qtd_as_of is None


def test_compare_kpi_filters_to_the_requested_tickers_case_insensitively(db_session):
    comparison = compare_kpi(db_session, "Total Revenue ($MM)", tickers=["beta", "ACME"])
    assert [r.ticker for r in comparison.companies] == ["ACME", "BETA"]


def test_compare_kpi_unknown_kpi_raises(db_session):
    with pytest.raises(NotFoundError):
        compare_kpi(db_session, "No Such KPI")


def test_compare_kpi_unknown_ticker_raises(db_session):
    with pytest.raises(NotFoundError):
        compare_kpi(db_session, "Total Revenue ($MM)", tickers=["ACME", "NOPE"])


def test_compare_kpi_runs_a_constant_number_of_queries(db_session, query_counter):
    """compare_kpi must not issue a query per company (no N+1).

    Four queries: resolve the KPI, resolve the companies, one batched history
    query, one batched QTD query. The count is fixed by the code, not by how
    many companies the comparison covers.
    """
    query_counter.count = 0
    compare_kpi(db_session, "Total Revenue ($MM)")
    assert query_counter.count == 4
