"""GET /overview: the glanceable summary, one card per (company, KPI) series."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app import service
from app.db import get_session
from app.schemas import OverviewResponse

router = APIRouter()


@router.get("/overview")
def get_overview(
    session: Annotated[Session, Depends(get_session)],
    search: Annotated[
        str | None, Query(description="Filter cards by ticker, name, sector, or KPI.")
    ] = None,
) -> OverviewResponse:
    """Return the overview cards, optionally narrowed by a search term.

    This is the glance tier of the UX: each card carries the latest closed
    quarter, the current QTD value and its as_of, and a short sparkline.
    """
    return service.get_overview(session, search=search)
