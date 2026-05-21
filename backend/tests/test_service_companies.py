"""Company lookups, KPI listing, and the overview assembly (with a no-N+1 check)."""

from datetime import date

import pytest

from app.errors import NotFoundError
from app.service import get_company, get_overview, list_companies, list_kpis


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


def test_overview_runs_a_constant_number_of_queries(db_session, query_counter):
    """get_overview must not issue a query per series (no N+1).

    Three queries: latest historical per series, current QTD per series, and the
    historical values for the sparklines. The count is fixed by the code, not by
    how many series the fixture holds.
    """
    query_counter.count = 0
    get_overview(db_session)
    assert query_counter.count == 3
