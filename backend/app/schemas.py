"""Pydantic models: the API contract shared by the REST routers and the MCP tools.

These are the request and response shapes. The service layer returns these
models, so both consumers receive identical, typed results.

A note on `value`. In the database it is `numeric` (exact, no float drift). The
request schema (`PublishEstimateRequest`) keeps `value` as a `Decimal`, so an
incoming JSON number is stored without a float round-trip. The response schemas
expose `value` as a `float`, because the chart and the CSV export need a number
and Pydantic would otherwise serialize a `Decimal` to a JSON string.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CompanySummary(BaseModel):
    """A company as it appears in a list or a search result."""

    model_config = ConfigDict(from_attributes=True)

    ticker: str
    name: str
    sector: str


class KpiInfo(BaseModel):
    """A KPI and the unit its values are measured in."""

    model_config = ConfigDict(from_attributes=True)

    name: str
    unit: str


class CompanyDetail(BaseModel):
    """One company and the KPIs it reports."""

    ticker: str
    name: str
    sector: str
    kpis: list[KpiInfo]


class EstimatePoint(BaseModel):
    """One closed-quarter historical estimate: a single point on the history line."""

    period: str
    period_start: date
    period_end: date
    value: float
    created_at: datetime


class QtdSnapshot(BaseModel):
    """One intra-quarter QTD snapshot, stamped with the as_of date it is effective for."""

    period: str
    period_start: date
    period_end: date
    value: float
    as_of: date
    created_at: datetime


class SeriesAnalytics(BaseModel):
    """Closed-quarter trend signals for a series, computed from the full history.

    `qoq` and `yoy` are fractional percent changes of the latest closed
    quarter's value: 0.05 means a +5% move. `qoq` compares it to the
    immediately preceding quarter, `yoy` to the same quarter one year earlier.
    A field is None when its comparison quarter is absent from the data or has a
    zero value, so the UI never shows a misleading number.

    Only closed-quarter (historical) estimates feed these signals. A QTD
    estimate is a partial, cumulative-to-date value, so it carries no YoY/QoQ.
    The signals are computed from the complete history, so they do not change
    when the chart's date filter narrows the view.
    """

    latest_period: str | None
    qoq: float | None
    yoy: float | None


class SeriesDetail(BaseModel):
    """The full (company, KPI) time series: closed-quarter history plus QTD snapshots.

    `current_qtd` is the snapshot with the latest `as_of`, surfaced here so the
    UI and the MCP tools never recompute it. `last_updated` is the most recent
    `created_at` across the series, the audit "last updated" timestamp.
    `analytics` carries the YoY/QoQ trend signals for the series.
    """

    ticker: str
    company_name: str
    kpi: str
    unit: str
    history: list[EstimatePoint]
    qtd_snapshots: list[QtdSnapshot]
    current_qtd: QtdSnapshot | None
    last_updated: datetime | None
    analytics: SeriesAnalytics


class CompanyEstimates(BaseModel):
    """Every KPI series for one company: the answer to "all estimates for a company"."""

    ticker: str
    company_name: str
    sector: str
    series: list[SeriesDetail]


class OverviewCard(BaseModel):
    """One glanceable summary card: a single (company, KPI) series at a glance."""

    ticker: str
    company_name: str
    sector: str
    kpi: str
    unit: str
    latest_historical_value: float | None
    latest_historical_period: str | None
    current_qtd_value: float | None
    current_qtd_as_of: date | None
    sparkline: list[float]


class OverviewResponse(BaseModel):
    """The overview: one card per (company, KPI) series."""

    cards: list[OverviewCard]


class KpiComparisonRow(BaseModel):
    """One company's standing on a single KPI, for a peer comparison.

    Carries the latest closed-quarter value, the current QTD value, and the
    YoY/QoQ trend signals, so several rows line up into a comparison table. A
    value field is null when the company has no data for that part.
    """

    ticker: str
    company_name: str
    sector: str
    latest_historical_value: float | None
    latest_historical_period: str | None
    current_qtd_value: float | None
    current_qtd_as_of: date | None
    analytics: SeriesAnalytics


class KpiComparison(BaseModel):
    """One KPI compared across several companies: the peer-scan result.

    `kpi` and `unit` are stated once, since every row shares them; `companies`
    holds one row per company, sorted by ticker.
    """

    kpi: str
    unit: str
    companies: list[KpiComparisonRow]


class PublishEstimateRequest(BaseModel):
    """The body of POST /estimates: a new estimate to append.

    Every field and cross-field rule is validated here, so an invalid request
    fails fast as an HTTP 422 before the service layer runs. The service layer
    only checks that the ticker and the KPI exist.
    """

    ticker: str = Field(min_length=1, max_length=16)
    kpi: str = Field(min_length=1, max_length=64)
    # period is a quarter code like "2026Q1". The pattern keeps a malformed or
    # hostile value (a CSV-formula string, say) out of the stored data.
    period: str = Field(pattern=r"^\d{4}Q[1-4]$")
    period_start: date
    period_end: date
    estimate_type: Literal["historical", "qtd"]
    value: Decimal = Field(ge=0, max_digits=20, decimal_places=4)
    as_of: date | None = None

    @model_validator(mode="after")
    def _check_consistency(self) -> "PublishEstimateRequest":
        """Enforce the period ordering and the as_of invariants.

        This mirrors the database CHECK constraints: a qtd estimate is a snapshot
        and must carry an as_of date; a historical estimate is a closed quarter
        and must not. A qtd as_of must also fall inside the period window: the
        current-QTD resolution orders by as_of, so an as_of outside the quarter
        (a far-future date in particular) would permanently win that resolution.
        """
        if self.period_end < self.period_start:
            raise ValueError("period_end must not precede period_start")
        if self.estimate_type == "qtd" and self.as_of is None:
            raise ValueError("a qtd estimate requires an as_of date")
        if (
            self.estimate_type == "qtd"
            and self.as_of is not None
            and not (self.period_start <= self.as_of <= self.period_end)
        ):
            raise ValueError("a qtd as_of must fall within the period window")
        if self.estimate_type == "historical" and self.as_of is not None:
            raise ValueError("a historical estimate must not carry an as_of date")
        return self


class EstimateRecord(BaseModel):
    """The response of POST /estimates: the row that was appended, echoed back.

    `id` and `created_at` are assigned by the server, so the caller learns both.
    """

    id: int
    ticker: str
    kpi: str
    period: str
    period_start: date
    period_end: date
    estimate_type: str
    value: float
    as_of: date | None
    created_at: datetime
