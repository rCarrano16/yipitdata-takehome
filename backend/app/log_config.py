"""Structured JSON logging: one JSON object per line on stdout.

Every log line is a single JSON object, so a log aggregator can parse it
without a custom pattern. The per-request `request_id` is carried in a
contextvar (`request_id_var`): the request-logging middleware sets it at the
start of each request, and this formatter reads it, so every line emitted while
that request is handled, including the service layer's own audit lines, carries
the same id and can be correlated after the fact.
"""

import json
import logging
import sys
from contextvars import ContextVar
from datetime import UTC, datetime

from app.config import settings

# Set by the request-logging middleware, read by JsonFormatter. The default is
# None so lines logged outside any request (startup, the seed script) still
# format cleanly instead of raising for a missing value.
request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)

# Optional fields the middleware attaches via `extra=`. A line logged without
# them (for example the service layer's audit line) simply omits them.
_OPTIONAL_FIELDS = ("method", "path", "status", "latency_ms")


class JsonFormatter(logging.Formatter):
    """Render a LogRecord as a single-line JSON object."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        request_id = request_id_var.get()
        if request_id is not None:
            payload["request_id"] = request_id
        # getattr with a default: a record without these attributes is normal,
        # so the formatter must never assume they are present.
        for field in _OPTIONAL_FIELDS:
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload)


def configure_logging() -> None:
    """Send all logging through one stdout handler that emits JSON.

    Called once when the application module is imported. It also re-points
    uvicorn's own loggers at this handler, so the server's startup and error
    lines are JSON too, rather than plaintext mixed into the structured stream.
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(settings.log_level.upper())

    # uvicorn installs its own handlers; clear them and let its loggers
    # propagate to the root JSON handler instead. The access logger is disabled
    # at the command line (--no-access-log): the request-logging middleware is
    # the access log, so uvicorn's plaintext one would only duplicate it.
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        uvicorn_logger = logging.getLogger(name)
        uvicorn_logger.handlers.clear()
        uvicorn_logger.propagate = True
