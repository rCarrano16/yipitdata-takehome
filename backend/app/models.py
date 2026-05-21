"""SQLAlchemy ORM models: the database schema for the KPI estimates portal.

Three tables: companies and kpis are first-class entities, and estimates holds
both closed-quarter (historical) and intra-quarter (qtd) rows, discriminated by
estimate_type. The schema has no ORM relationships on purpose: every service
query is an explicit select with an explicit join, so relationships would be
unused surface and would invite accidental lazy-load N+1 reads.
"""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative base. Its metadata drives create_all in the seed script."""


class Company(Base):
    """A public company that reports KPI estimates."""

    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticker: Mapped[str] = mapped_column(String(16), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    sector: Mapped[str] = mapped_column(String(64), nullable=False)

    # Search and the overview filter by sector, so it gets its own index.
    __table_args__ = (Index("ix_companies_sector", "sector"),)


class Kpi(Base):
    """A key performance indicator, for example "Total Revenue ($MM)"."""

    __tablename__ = "kpis"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    # The unit lives on the KPI because KPI-to-unit is a fixed 1:1 mapping.
    unit: Mapped[str] = mapped_column(String(16), nullable=False)

    __table_args__ = (
        CheckConstraint("unit IN ('$', '$MM', 'subs', 'units')", name="ck_kpis_unit"),
    )


class Estimate(Base):
    """One KPI estimate: a closed-quarter value (historical) or an intra-quarter
    snapshot (qtd). The estimate_type column discriminates the two."""

    __tablename__ = "estimates"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False)
    kpi_id: Mapped[int] = mapped_column(ForeignKey("kpis.id"), nullable=False)
    period: Mapped[str] = mapped_column(String(8), nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    estimate_type: Mapped[str] = mapped_column(String(16), nullable=False)
    # Numeric, not float: financial values must not carry binary rounding drift.
    value: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    # as_of is the QTD snapshot's effective date. Null for historical rows.
    as_of: Mapped[date | None] = mapped_column(Date, nullable=True)
    # created_at is the audit timestamp: when the row was written, set server-side.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint("estimate_type IN ('historical', 'qtd')", name="ck_estimates_type"),
        CheckConstraint("value >= 0", name="ck_estimates_value_nonnegative"),
        # The core QTD invariant: historical rows carry no as_of, qtd rows must.
        CheckConstraint(
            "(estimate_type = 'historical' AND as_of IS NULL) "
            "OR (estimate_type = 'qtd' AND as_of IS NOT NULL)",
            name="ck_estimates_as_of_matches_type",
        ),
    )


# Indexes for the Estimate table are declared here, after the class, so the
# descending columns of the partial index can use real column expressions
# instead of stringly-typed SQL text.

# Primary access path: reads for one company, or for one (company, KPI) series.
Index("ix_estimates_company_kpi", Estimate.company_id, Estimate.kpi_id)

# Supports the QTD reads. Partial: it indexes qtd rows only, since historical
# rows never take this path. It leads with (company_id, kpi_id), the equality
# filter both QTD queries apply, then carries as_of and created_at, the columns
# the latest-snapshot resolution sorts on. The id tiebreak is not indexed;
# Postgres applies it as a cheap final sort over the few rows of one series.
Index(
    "ix_estimates_qtd_latest",
    Estimate.company_id,
    Estimate.kpi_id,
    Estimate.as_of.desc(),
    Estimate.created_at.desc(),
    postgresql_where=(Estimate.estimate_type == "qtd"),
)
