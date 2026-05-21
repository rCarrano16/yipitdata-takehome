"""Idempotent loader for the sample KPI data: CSV into PostgreSQL.

Run as a module:   python -m app.seed [--force] [--csv PATH]
Import and call:   from app.seed import seed; seed()

The schema is created here, via create_all; there is no separate migration tool.
The load is idempotent: it is skipped when estimates already holds rows, unless
--force is given, which truncates the three tables and reloads from scratch.
"""

import argparse
import csv
import logging
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.db import engine, session_scope
from app.log_config import configure_logging
from app.models import Base, Company, Estimate, Kpi

logger = logging.getLogger("app.seed")

# The CSV ships in the repo at data/; the repo root is three levels up.
_REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CSV_PATH = _REPO_ROOT / "data" / "kpi_sample_2000.csv"

_VALID_UNITS = {"$", "$MM", "subs", "units"}
_VALID_ESTIMATE_TYPES = {"historical", "qtd"}
_REQUIRED_FIELDS = (
    "company_name",
    "ticker",
    "sector",
    "kpi",
    "period_start",
    "period_end",
    "period",
    "estimate_type",
    "value",
    "unit",
)


def _parse_row(row: dict, line_no: int) -> dict:
    """Validate one CSV row and return it with native Python types.

    Raises ValueError, naming the line number, on any invalid field.
    """
    for field in _REQUIRED_FIELDS:
        if not (row.get(field) or "").strip():
            raise ValueError(f"line {line_no}: missing required field '{field}'")

    estimate_type = row["estimate_type"].strip()
    if estimate_type not in _VALID_ESTIMATE_TYPES:
        raise ValueError(f"line {line_no}: invalid estimate_type '{estimate_type}'")

    unit = row["unit"].strip()
    if unit not in _VALID_UNITS:
        raise ValueError(f"line {line_no}: invalid unit '{unit}'")

    raw_value = row["value"].strip()
    try:
        value = Decimal(raw_value)
    except InvalidOperation:
        raise ValueError(f"line {line_no}: value '{raw_value}' is not a number") from None
    if not value.is_finite():
        raise ValueError(f"line {line_no}: value '{raw_value}' is not finite")
    if value < 0:
        raise ValueError(f"line {line_no}: value must be non-negative, got {value}")

    try:
        period_start = date.fromisoformat(row["period_start"].strip())
        period_end = date.fromisoformat(row["period_end"].strip())
    except ValueError as exc:
        raise ValueError(f"line {line_no}: invalid period date ({exc})") from None
    if period_end < period_start:
        raise ValueError(
            f"line {line_no}: period_end {period_end} precedes period_start {period_start}"
        )

    raw_as_of = (row.get("as_of") or "").strip()
    if estimate_type == "historical":
        if raw_as_of:
            raise ValueError(f"line {line_no}: historical row must not have an as_of")
        as_of: date | None = None
    else:  # estimate_type == "qtd"
        if not raw_as_of:
            raise ValueError(f"line {line_no}: qtd row must have an as_of")
        try:
            as_of = date.fromisoformat(raw_as_of)
        except ValueError:
            raise ValueError(f"line {line_no}: invalid as_of '{raw_as_of}'") from None

    return {
        "company_name": row["company_name"].strip(),
        "ticker": row["ticker"].strip(),
        "sector": row["sector"].strip(),
        "kpi": row["kpi"].strip(),
        "unit": unit,
        "period": row["period"].strip(),
        "period_start": period_start,
        "period_end": period_end,
        "estimate_type": estimate_type,
        "value": value,
        "as_of": as_of,
    }


def _read_csv(csv_path: Path) -> list[dict]:
    """Read and validate every CSV row. Raises if the file or any row is invalid."""
    if not csv_path.is_file():
        raise FileNotFoundError(f"CSV not found: {csv_path}")
    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        # enumerate from 2: line 1 of the file is the header.
        rows = [_parse_row(row, line_no) for line_no, row in enumerate(reader, start=2)]
    if not rows:
        raise ValueError(f"CSV has no data rows: {csv_path}")
    return rows


def _insert_companies(session: Session, rows: list[dict]) -> dict[str, Company]:
    """Insert one Company per unique ticker. Returns a ticker -> Company map."""
    companies: dict[str, Company] = {}
    for r in rows:
        ticker = r["ticker"]
        if ticker not in companies:
            companies[ticker] = Company(ticker=ticker, name=r["company_name"], sector=r["sector"])
        else:
            # A ticker must always carry the same name and sector.
            seen = companies[ticker]
            if seen.name != r["company_name"] or seen.sector != r["sector"]:
                raise ValueError(f"ticker '{ticker}' has inconsistent name or sector")
    session.add_all(companies.values())
    return companies


def _insert_kpis(session: Session, rows: list[dict]) -> dict[str, Kpi]:
    """Insert one Kpi per unique name. Returns a kpi-name -> Kpi map.

    Enforces the KPI-to-unit 1:1 invariant: one KPI name always has one unit.
    """
    kpis: dict[str, Kpi] = {}
    for r in rows:
        name = r["kpi"]
        if name not in kpis:
            kpis[name] = Kpi(name=name, unit=r["unit"])
        elif kpis[name].unit != r["unit"]:
            raise ValueError(f"kpi '{name}' has two units: '{kpis[name].unit}' and '{r['unit']}'")
    session.add_all(kpis.values())
    return kpis


def seed(csv_path: Path = DEFAULT_CSV_PATH, force: bool = False) -> None:
    """Create the schema and load the sample CSV into the database.

    Idempotent: if estimates already holds rows the load is skipped, unless force
    is set, in which case the three tables are truncated and reloaded.
    """
    Base.metadata.create_all(engine)

    with session_scope() as session:
        existing = session.scalar(select(func.count()).select_from(Estimate)) or 0
        if existing and not force:
            logger.info("seed skipped: estimates already has %d rows", existing)
            return
        if existing and force:
            logger.info("force: clearing %d existing estimate rows", existing)
            session.execute(text("TRUNCATE estimates, kpis, companies RESTART IDENTITY CASCADE"))

        rows = _read_csv(csv_path)
        companies = _insert_companies(session, rows)
        kpis = _insert_kpis(session, rows)
        session.flush()  # assign the generated company and KPI primary keys

        session.add_all(
            Estimate(
                company_id=companies[r["ticker"]].id,
                kpi_id=kpis[r["kpi"]].id,
                period=r["period"],
                period_start=r["period_start"],
                period_end=r["period_end"],
                estimate_type=r["estimate_type"],
                value=r["value"],
                as_of=r["as_of"],
            )
            for r in rows
        )
        counts = (len(companies), len(kpis), len(rows))

    # Logged only here, after the session_scope block committed successfully.
    logger.info("seed complete: %d companies, %d kpis, %d estimates", *counts)


def main() -> None:
    """Command-line entry point for `python -m app.seed`."""
    # Route the seed's own log lines through the JSON handler, so the seed step
    # in the Docker start command emits the same structured format as the API.
    configure_logging()
    parser = argparse.ArgumentParser(description="Seed the KPI database from the sample CSV.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Truncate existing data and reload from scratch.",
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=DEFAULT_CSV_PATH,
        help=f"Path to the CSV file (default: {DEFAULT_CSV_PATH}).",
    )
    args = parser.parse_args()
    seed(csv_path=args.csv, force=args.force)


if __name__ == "__main__":
    main()
