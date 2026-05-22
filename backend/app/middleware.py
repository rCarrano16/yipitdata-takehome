"""Request-logging middleware: one structured line per request.

For every request it generates (or reuses) a request id, times the request,
emits a single JSON log line, and returns the id in the `X-Request-ID` response
header. An unhandled error is logged as a 500 before being re-raised, so the
failures that matter most are never missing from the log.
"""

import logging
import time
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.log_config import request_id_var

logger = logging.getLogger("app.request")

# Health and metrics are polled constantly (a load balancer hits /health,
# Prometheus scrapes /metrics). A successful request to either is logged at
# DEBUG, not INFO, so the steady probe traffic does not bury the real request
# log. A failure on either path is still logged as a 500 by _log_failure.
_QUIET_PATHS = frozenset({"/health", "/metrics"})


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Time each request, log it as one JSON line, and stamp X-Request-ID."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Reuse an inbound request id if the caller sent one (trace continuity
        # across services), otherwise mint a fresh one.
        request_id = request.headers.get("X-Request-ID") or str(uuid4())
        # request.state survives into the exception handlers; the contextvar
        # below is reset before ServerErrorMiddleware runs, so the 500 handler
        # reads the id from state instead.
        request.state.request_id = request_id
        token = request_id_var.set(request_id)
        start = time.perf_counter()
        try:
            try:
                response = await call_next(request)
            except Exception:
                # An unhandled error from the route or a downstream middleware.
                self._log_failure(request, start)
                raise
            # call_next succeeded. Stamping the response and emitting the
            # success line is wrapped too, so a failure here (a logging error,
            # say) is still logged as a 500 instead of escaping unlogged.
            try:
                response.headers["X-Request-ID"] = request_id
                latency_ms = round((time.perf_counter() - start) * 1000, 2)
                # Quiet paths drop to DEBUG; logger.log takes the level as an
                # argument so the success line stays a single call site.
                level = logging.DEBUG if request.url.path in _QUIET_PATHS else logging.INFO
                logger.log(
                    level,
                    "request",
                    extra={
                        "method": request.method,
                        "path": request.url.path,
                        "status": response.status_code,
                        "latency_ms": latency_ms,
                    },
                )
            except Exception:
                self._log_failure(request, start)
                raise
            return response
        finally:
            # Reset last, so every log line above still carries the request id.
            request_id_var.reset(token)

    @staticmethod
    def _log_failure(request: Request, start: float) -> None:
        """Log an unhandled error as a 500.

        Called from an except block, so logger.exception records the traceback.
        The outer ServerErrorMiddleware builds the actual 500 response; this
        only guarantees the failure is never missing from the log.
        """
        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.exception(
            "request failed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status": 500,
                "latency_ms": latency_ms,
            },
        )
