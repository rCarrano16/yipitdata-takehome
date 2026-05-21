"""GET /kpis: list every KPI and its unit."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import service
from app.db import get_session
from app.schemas import KpiInfo

router = APIRouter()


@router.get("/kpis")
def list_kpis(session: Annotated[Session, Depends(get_session)]) -> list[KpiInfo]:
    """Return all KPI names and their units, so a client can discover them."""
    return service.list_kpis(session)
