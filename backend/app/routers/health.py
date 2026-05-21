"""GET /health: a liveness check plus a database connectivity probe."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_session

router = APIRouter()
logger = logging.getLogger("app.health")


class HealthStatus(BaseModel):
    """The /health response body: overall status and the database probe result.

    Declared so the endpoint publishes a real OpenAPI response schema. It is an
    operational shape, not domain data, so it lives here and not in schemas.py.
    """

    status: str
    db: str


@router.get("/health", response_model=HealthStatus, responses={503: {"model": HealthStatus}})
def health(session: Annotated[Session, Depends(get_session)]) -> JSONResponse:
    """Report whether the service and its database are reachable.

    Returns 200 with {"status": "ok", "db": "ok"} when a trivial query
    succeeds, and 503 with {"status": "error", "db": "error"} when it does not,
    so a load balancer or an uptime monitor can act on the status code alone.
    The body is returned on both paths via an explicit JSONResponse.
    """
    try:
        session.execute(text("SELECT 1"))
    except Exception:
        logger.exception("health check failed: database unreachable")
        return JSONResponse(status_code=503, content={"status": "error", "db": "error"})
    return JSONResponse(status_code=200, content={"status": "ok", "db": "ok"})
