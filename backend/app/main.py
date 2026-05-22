"""FastAPI application: wires routers, middleware, logging, and error handling.

There is no app factory. `app` is a plain module-level object, which is all
uvicorn and the test client need; tests swap the database session through
`app.dependency_overrides`, which works fine on a module-level app.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

from app.config import settings
from app.errors import NotFoundError
from app.log_config import configure_logging
from app.middleware import RequestLoggingMiddleware
from app.routers import companies, estimates, health, kpis, overview

# Configure JSON logging before the app is built, so every later line is JSON.
configure_logging()

app = FastAPI(
    title="KPI Estimates Portal API",
    version="0.1.0",
    description="Quarterly KPI estimates for time-constrained public-market investors.",
)

# Middleware is applied outermost-last. CORS is added first, the Prometheus
# metrics middleware next, and the request-logging middleware last, so logging
# stays the outer layer: it times the whole request and sees the final,
# CORS-decorated response.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    # The browser frontend is read-only, so only GET is allowed cross-origin.
    # Publishing is a separate ingestion path that does not run in the browser.
    allow_methods=["GET"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

# Prometheus metrics. instrument() adds the metrics-collecting middleware;
# expose() publishes GET /metrics for Prometheus to scrape. The scrape endpoint
# is excluded from its own metrics and from the OpenAPI schema, since it is an
# operational endpoint, not part of the JSON data API.
Instrumentator(excluded_handlers=["/metrics"]).instrument(app).expose(app, include_in_schema=False)

app.add_middleware(RequestLoggingMiddleware)


@app.exception_handler(NotFoundError)
async def handle_not_found(request: Request, exc: NotFoundError) -> JSONResponse:
    """Map the single domain exception to a 404.

    Body and field validation errors raise pydantic.ValidationError, which
    FastAPI already maps to 422, so they need no handler here.
    """
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(Exception)
async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    """Return a consistent JSON 500 for any otherwise-unhandled error.

    Without this, Starlette's ServerErrorMiddleware answers with a plain-text
    body, leaving the error contract inconsistent (404 and 422 are JSON). The
    request-logging middleware has already logged the exception with its
    traceback; this handler only shapes the response. The detail is generic on
    purpose: an unexpected error must not leak internals to the caller. The
    request id comes from request.state, since the contextvar is already reset.
    """
    request_id = getattr(request.state, "request_id", None)
    headers = {"X-Request-ID": request_id} if request_id else None
    return JSONResponse(
        status_code=500,
        content={"detail": "internal server error"},
        headers=headers,
    )


app.include_router(health.router)
app.include_router(overview.router)
app.include_router(companies.router)
app.include_router(kpis.router)
app.include_router(estimates.router)
