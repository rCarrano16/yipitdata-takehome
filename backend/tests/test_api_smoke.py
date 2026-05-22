"""Router-level smoke tests: status codes and response shapes for every endpoint.

These exercise the full FastAPI stack (routing, middleware, exception handlers)
through a TestClient. The deeper query and QTD behavior is already covered by
the service-layer tests; here the focus is that each route is wired correctly.
"""

import logging

from fastapi.testclient import TestClient
from prometheus_client import REGISTRY

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
        "as_of": "2026-03-20",
    }
    body.update(overrides)
    return body


def test_health_reports_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "db": "ok"}


def test_health_publishes_a_response_schema(client):
    """The /health endpoint documents its body in the OpenAPI schema.

    Declaring the HealthStatus model gives the 200 response a real schema; with
    a bare JSONResponse return type the schema would be empty.
    """
    openapi = client.get("/openapi.json").json()
    ok_response = openapi["paths"]["/health"]["get"]["responses"]["200"]
    assert "schema" in ok_response["content"]["application/json"]


def test_health_reports_503_when_the_database_is_unreachable(client, db_session, monkeypatch):
    """The /health 503 path: a failing database probe returns 503, not 200.

    503 is the status a load balancer or uptime monitor acts on. The session's
    execute is patched to raise, simulating an unreachable database; the route
    must catch it and answer 503 with the error body.
    """

    def _boom(*args, **kwargs):
        raise RuntimeError("simulated database failure")

    monkeypatch.setattr(db_session, "execute", _boom)
    response = client.get("/health")

    assert response.status_code == 503
    assert response.json() == {"status": "error", "db": "error"}


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
    assert series["current_qtd"]["as_of"] == "2026-03-20"
    assert series["current_qtd"]["value"] == 99.5


def test_publish_qtd_without_as_of_is_422(client):
    response = client.post("/estimates", json=_publish_body(as_of=None))
    assert response.status_code == 422


def test_publish_qtd_as_of_outside_period_window_is_422(client):
    # as_of past period_end: the schema rejects it before it reaches the service.
    response = client.post("/estimates", json=_publish_body(as_of="2026-04-15"))
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


def test_metrics_endpoint_is_exposed(client):
    """GET /metrics serves the Prometheus exposition for the scraper."""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    # The exposition always carries HELP/TYPE comment lines.
    assert "# HELP" in response.text


def test_publish_increments_the_metrics_counter(client):
    """A successful publish bumps the kpi_estimates_published_total counter.

    The counter is process-global and not transactional, so it is read before
    and after and asserted to have moved by exactly one; the absolute value
    depends on how many other tests published first.
    """
    labels = {"estimate_type": "qtd"}
    before = REGISTRY.get_sample_value("kpi_estimates_published_total", labels) or 0.0

    response = client.post("/estimates", json=_publish_body())
    assert response.status_code == 201

    after = REGISTRY.get_sample_value("kpi_estimates_published_total", labels)
    assert after == before + 1


def test_quiet_paths_are_not_logged_at_info(client, caplog):
    """Health and metrics probes are logged at DEBUG, not INFO.

    Both are polled constantly, so logging them at INFO would bury the real
    request log. A normal endpoint is still logged at INFO.
    """
    with caplog.at_level(logging.INFO, logger="app.request"):
        client.get("/health")
        client.get("/metrics")
        quiet = [r for r in caplog.records if r.name == "app.request"]
        assert quiet == []

        client.get("/kpis")
        logged = [r for r in caplog.records if r.name == "app.request"]
        assert [r.getMessage() for r in logged] == ["request"]


def test_error_inside_middleware_body_returns_consistent_json_500(db_session, monkeypatch):
    """An error raised in the logging middleware itself still yields a JSON 500.

    The test above covers a failure inside call_next (the route). This covers
    the other path: a failure in the middleware's own body, after call_next has
    returned. The catch-all handler must shape it the same way.
    """

    def _boom(*args, **kwargs):
        raise RuntimeError("simulated middleware failure")

    # logger.log emits the request line in the middleware body once call_next
    # has succeeded; patching it makes that body raise.
    monkeypatch.setattr("app.middleware.logger.log", _boom)
    app.dependency_overrides[get_session] = lambda: db_session
    try:
        with TestClient(app, raise_server_exceptions=False) as raising_client:
            response = raising_client.get("/health")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 500
    assert response.json() == {"detail": "internal server error"}
    assert response.headers.get("X-Request-ID")
