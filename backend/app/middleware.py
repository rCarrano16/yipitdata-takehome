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
            response = await call_next(request)
        except Exception:
            # An unhandled error: log it as a 500 here (the outer
            # ServerErrorMiddleware builds the actual 500 response), then
            # re-raise so error handling is not swallowed.
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
            raise
        else:
            latency_ms = round((time.perf_counter() - start) * 1000, 2)
            response.headers["X-Request-ID"] = request_id
            logger.info(
                "request",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status": response.status_code,
                    "latency_ms": latency_ms,
                },
            )
            return response
        finally:
            request_id_var.reset(token)
