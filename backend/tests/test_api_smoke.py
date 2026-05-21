"""Router-level smoke tests: status codes and response shapes for every endpoint.

These exercise the full FastAPI stack (routing, middleware, exception handlers)
through a TestClient. The deeper query and QTD behavior is already covered by
the service-layer tests; here the focus is that each route is wired correctly.
"""

from fastapi.testclient import TestClient

from app import service
from app.db import get_session
from app.main import app


def _publish_body(**overrides) -> dict:
    """A valid QTD publish body as JSON-ready primitives, with optional overrides."""
    body = {
        "ticker": "ACME",
        "kpi": "Total Revenue ($MM)",
        "period": "2026Q1",
        "period_start": "2026-01-01",
        "period_end": "2026-03-31",
        "estimate_type": "qtd",
        "value": 99.5,
        "as_of": "2026-04-01",
    }
    body.update(overrides)
    return body


def test_health_reports_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "db": "ok"}


def test_response_carries_request_id_header(client):
    response = client.get("/health")
    assert response.headers.get("X-Request-ID")


def test_overview_returns_one_card_per_series(client):
    response = client.get("/overview")
    assert response.status_code == 200
    cards = response.json()["cards"]
    keys = {(c["ticker"], c["kpi"]) for c in cards}
    assert keys == {
        ("ACME", "Total Revenue ($MM)"),
        ("ACME", "Units Sold"),
        ("GAMM", "Total Revenue ($MM)"),
        ("BETA", "Total Revenue ($MM)"),
    }


def test_overview_search_filters_cards(client):
    response = client.get("/overview", params={"search": "retail"})
    assert response.status_code == 200
    assert {c["ticker"] for c in response.json()["cards"]} == {"BETA"}


def test_list_companies_returns_all(client):
    response = client.get("/companies")
    assert response.status_code == 200
    assert {c["ticker"] for c in response.json()} == {"ACME", "BETA", "GAMM"}


def test_list_companies_search_matches_sector(client):
    response = client.get("/companies", params={"search": "cloud"})
    assert response.status_code == 200
    assert {c["ticker"] for c in response.json()} == {"ACME", "GAMM"}


def test_get_company_lists_its_kpis(client):
    response = client.get("/companies/ACME")
    assert response.status_code == 200
    body = response.json()
    assert body["ticker"] == "ACME"
    assert {k["name"] for k in body["kpis"]} == {"Total Revenue ($MM)", "Units Sold"}


def test_get_company_unknown_ticker_is_404(client):
    response = client.get("/companies/NOPE")
    assert response.status_code == 404
    assert "detail" in response.json()


def test_get_company_estimates_returns_every_series(client):
    response = client.get("/companies/ACME/estimates")
    assert response.status_code == 200
    body = response.json()
    assert body["ticker"] == "ACME"
    assert len(body["series"]) == 2


def test_get_series_returns_history_and_qtd(client):
    response = client.get("/companies/ACME/kpis/Total Revenue ($MM)")
    assert response.status_code == 200
    body = response.json()
    assert len(body["history"]) == 3
    assert len(body["qtd_snapshots"]) == 3
    assert body["current_qtd"]["as_of"] == "2026-03-15"


def test_get_series_date_filter_narrows_qtd(client):
    response = client.get(
        "/companies/ACME/kpis/Total Revenue ($MM)",
        params={"from": "2026-01-31", "to": "2026-02-15"},
    )
    assert response.status_code == 200
    as_ofs = [s["as_of"] for s in response.json()["qtd_snapshots"]]
    assert as_ofs == ["2026-01-31", "2026-02-15"]


def test_get_series_unknown_kpi_is_404(client):
    response = client.get("/companies/ACME/kpis/No Such KPI")
    assert response.status_code == 404


def test_list_kpis_returns_names_and_units(client):
    response = client.get("/kpis")
    assert response.status_code == 200
    assert {k["name"]: k["unit"] for k in response.json()} == {
        "Total Revenue ($MM)": "$MM",
        "Units Sold": "units",
    }


def test_publish_estimate_appends_and_becomes_current_qtd(client):
    response = client.post("/estimates", json=_publish_body())
    assert response.status_code == 201
    record = response.json()
    assert record["id"] is not None
    assert record["value"] == 99.5

    # The newer as_of makes the published snapshot the current QTD on re-read.
    series = client.get("/companies/ACME/kpis/Total Revenue ($MM)").json()
    assert series["current_qtd"]["as_of"] == "2026-04-01"
    assert series["current_qtd"]["value"] == 99.5


def test_publish_qtd_without_as_of_is_422(client):
    response = client.post("/estimates", json=_publish_body(as_of=None))
    assert response.status_code == 422


def test_publish_unknown_ticker_is_404(client):
    response = client.post("/estimates", json=_publish_body(ticker="NOPE"))
    assert response.status_code == 404


def test_unexpected_error_returns_consistent_json_500(db_session, monkeypatch):
    """An unhandled error yields a JSON 500 with the request id, like 404/422.

    The route's service call is monkeypatched to raise. The 500 handler must
    answer with the same {"detail": ...} shape as the other errors, not the
    plain-text body Starlette would produce by default.
    """

    def _boom(*args, **kwargs):
        raise RuntimeError("simulated failure")

    monkeypatch.setattr(service, "list_kpis", _boom)
    app.dependency_overrides[get_session] = lambda: db_session
    try:
        # raise_server_exceptions=False so the client returns the 500 response
        # instead of re-raising the simulated error into the test.
        with TestClient(app, raise_server_exceptions=False) as raising_client:
            response = raising_client.get("/kpis")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 500
    assert response.json() == {"detail": "internal server error"}
    assert response.headers.get("X-Request-ID")
