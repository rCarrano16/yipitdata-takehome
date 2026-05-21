"""Company endpoints: list and search, detail, all estimates, and one series."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app import service
from app.db import get_session
from app.schemas import CompanyDetail, CompanyEstimates, CompanySummary, SeriesDetail

router = APIRouter(prefix="/companies")


@router.get("")
def list_companies(
    session: Annotated[Session, Depends(get_session)],
    search: Annotated[str | None, Query(description="Filter by ticker, name, or sector.")] = None,
) -> list[CompanySummary]:
    """List companies, optionally narrowed by a case-insensitive search."""
    return service.list_companies(session, search=search)


@router.get("/{ticker}")
def get_company(
    ticker: str,
    session: Annotated[Session, Depends(get_session)],
) -> CompanyDetail:
    """Return one company and the KPIs it reports. 404 if the ticker is unknown."""
    return service.get_company(session, ticker)


@router.get("/{ticker}/estimates")
def get_company_estimates(
    ticker: str,
    session: Annotated[Session, Depends(get_session)],
    date_from: Annotated[date | None, Query(alias="from")] = None,
    date_to: Annotated[date | None, Query(alias="to")] = None,
) -> CompanyEstimates:
    """Return every KPI series for one company. 404 if the ticker is unknown.

    `from` and `to` are inclusive date bounds. Each point is filtered by the
    date the chart plots it at: historical by period_end, QTD by as_of.
    """
    return service.get_company_estimates(session, ticker, date_from=date_from, date_to=date_to)


@router.get("/{ticker}/kpis/{kpi}")
def get_series(
    ticker: str,
    kpi: str,
    session: Annotated[Session, Depends(get_session)],
    date_from: Annotated[date | None, Query(alias="from")] = None,
    date_to: Annotated[date | None, Query(alias="to")] = None,
) -> SeriesDetail:
    """Return one (company, KPI) series: history, QTD snapshots, current QTD.

    This is the drill-down behind the detailed history-vs-QTD chart. 404 if the
    ticker or the KPI is unknown. `from` and `to` are inclusive date bounds.
    """
    return service.get_series(session, ticker, kpi, date_from=date_from, date_to=date_to)
