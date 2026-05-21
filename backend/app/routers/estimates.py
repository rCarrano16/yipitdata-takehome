"""POST /estimates: publish (append) a new estimate."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app import service
from app.db import get_session
from app.schemas import EstimateRecord, PublishEstimateRequest

router = APIRouter()


@router.post("/estimates", status_code=status.HTTP_201_CREATED)
def publish_estimate(
    payload: PublishEstimateRequest,
    session: Annotated[Session, Depends(get_session)],
) -> EstimateRecord:
    """Append one estimate and return the stored row.

    Publishing is append-only. PublishEstimateRequest fully validates the body
    (any violation is a 422); the service layer adds the ticker and KPI
    existence check (a 404). This router owns the transaction: it commits after
    the service call, because get_session never commits on its own.
    """
    record = service.publish_estimate(session, payload)
    session.commit()
    return record
