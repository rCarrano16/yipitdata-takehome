"""Publish: append-only inserts, with field validation owned by the request schema.

The request schema (PublishEstimateRequest) rejects bad fields on construction,
raising pydantic.ValidationError. The service layer only adds the existence
check, raising NotFoundError for an unknown ticker or KPI.
"""

from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy import func, select

from app.errors import NotFoundError
from app.models import Estimate
from app.schemas import PublishEstimateRequest
from app.service import publish_estimate


def _qtd_payload(**overrides) -> dict:
    """A valid QTD publish payload, with optional field overrides."""
    payload = dict(
        ticker="ACME",
        kpi="Total Revenue ($MM)",
        period="2026Q1",
        period_start=date(2026, 1, 1),
        period_end=date(2026, 3, 31),
        estimate_type="qtd",
        value=Decimal("42"),
        as_of=date(2026, 3, 20),
    )
    payload.update(overrides)
    return payload


def test_publish_appends_exactly_one_row(db_session):
    before = db_session.scalar(select(func.count()).select_from(Estimate))
    record = publish_estimate(db_session, PublishEstimateRequest(**_qtd_payload()))
    after = db_session.scalar(select(func.count()).select_from(Estimate))

    assert after == before + 1
    assert record.id is not None
    assert record.ticker == "ACME"
    assert record.created_at is not None


def test_publish_does_not_mutate_existing_rows(db_session):
    existing_ids = set(db_session.scalars(select(Estimate.id)).all())
    publish_estimate(db_session, PublishEstimateRequest(**_qtd_payload()))
    after_ids = set(db_session.scalars(select(Estimate.id)).all())

    # Publish only adds: every prior row is still present.
    assert existing_ids.issubset(after_ids)
    assert len(after_ids) == len(existing_ids) + 1


def test_publish_unknown_ticker_raises_not_found(db_session):
    with pytest.raises(NotFoundError):
        publish_estimate(db_session, PublishEstimateRequest(**_qtd_payload(ticker="NOPE")))


def test_publish_unknown_kpi_raises_not_found(db_session):
    with pytest.raises(NotFoundError):
        publish_estimate(db_session, PublishEstimateRequest(**_qtd_payload(kpi="Made Up KPI")))


def test_qtd_without_as_of_is_rejected_by_the_schema():
    with pytest.raises(PydanticValidationError):
        PublishEstimateRequest(**_qtd_payload(as_of=None))


def test_historical_with_as_of_is_rejected_by_the_schema():
    with pytest.raises(PydanticValidationError):
        PublishEstimateRequest(**_qtd_payload(estimate_type="historical", as_of=date(2025, 12, 31)))


def test_negative_value_is_rejected_by_the_schema():
    with pytest.raises(PydanticValidationError):
        PublishEstimateRequest(**_qtd_payload(value=Decimal("-1")))


def test_period_end_before_start_is_rejected_by_the_schema():
    with pytest.raises(PydanticValidationError):
        PublishEstimateRequest(
            **_qtd_payload(period_start=date(2026, 3, 31), period_end=date(2026, 1, 1))
        )
