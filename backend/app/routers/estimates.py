"""POST /estimates: publish (append) a new estimate."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from prometheus_client import Counter
from sqlalchemy.orm import Session

from app import service
from app.db import get_session
from app.schemas import EstimateRecord, PublishEstimateRequest

router = APIRouter()

# A Prometheus counter for published estimates, labelled by estimate_type so a
# dashboard can split historical from qtd ingestion. Like every Prometheus
# metric it is process-global; the instrumentator in main.py exposes it on
# /metrics. The name is registered without the _total suffix, which the client
# appends in the exposition (so the scraped series is kpi_estimates_published_total).
estimates_published = Counter(
    "kpi_estimates_published",
    "Estimates published through POST /estimates.",
    ["estimate_type"],
)


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
    # Counted only after the commit succeeds: a 404 or 422 raises earlier, and a
    # commit failure raises above this line, so the metric tracks real writes.
    estimates_published.labels(estimate_type=payload.estimate_type).inc()
    return record
