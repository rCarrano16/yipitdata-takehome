"""Pytest fixtures: a real PostgreSQL test database, isolated per test.

The service layer leans on PostgreSQL features (DISTINCT ON, a partial index)
that SQLite does not have, so the tests run against a real database. They use a
separate `kpi_test` database in the same Docker Compose Postgres, so they never
touch development data.

Isolation strategy. The schema and a small deterministic fixture are created
once per test session. Each test then runs inside a transaction that is rolled
back at teardown, so a test never sees another test's writes and every test
starts from the identical seeded baseline.
"""

from collections.abc import Iterator
from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_session
from app.main import app
from app.models import Base, Company, Estimate, Kpi


def _test_database_url() -> str:
    """The kpi_test connection URL.

    Uses TEST_DATABASE_URL when set, otherwise the main DATABASE_URL with the
    database name swapped to kpi_test.
    """
    if settings.test_database_url:
        return settings.test_database_url
    return str(make_url(settings.database_url).set(database="kpi_test"))


def _ensure_database_exists(url: str) -> None:
    """Create the target database if it is absent.

    PostgreSQL cannot run CREATE DATABASE inside a transaction, so this opens an
    AUTOCOMMIT connection to the `postgres` maintenance database to do it.
    """
    url_obj = make_url(url)
    db_name = url_obj.database
    maintenance_engine = create_engine(
        url_obj.set(database="postgres"), isolation_level="AUTOCOMMIT"
    )
    try:
        with maintenance_engine.connect() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": db_name},
            ).scalar()
            if not exists:
                conn.execute(text(f'CREATE DATABASE "{db_name}"'))
    finally:
        maintenance_engine.dispose()


def _seed_fixture(session: Session) -> None:
    """Insert a small, deterministic dataset that covers the cases the tests need.

    Three companies (two share the Cloud sector, so a sector search returns
    two), two KPIs, and four (company, KPI) series chosen to exercise: history
    ordering, QTD resolution, out-of-order QTD insertion, a series with no QTD,
    and date-range filtering.
    """
    acme = Company(ticker="ACME", name="Acme Cloud Inc", sector="Cloud")
    gamm = Company(ticker="GAMM", name="Gamma Cloud Ltd", sector="Cloud")
    beta = Company(ticker="BETA", name="Beta Retail Co", sector="Retail")
    session.add_all([acme, gamm, beta])

    revenue = Kpi(name="Total Revenue ($MM)", unit="$MM")
    units = Kpi(name="Units Sold", unit="units")
    session.add_all([revenue, units])
    session.flush()  # assign the company and KPI ids used below

    def historical(
        company: Company, kpi: Kpi, period: str, start: date, end: date, value: str
    ) -> Estimate:
        return Estimate(
            company_id=company.id,
            kpi_id=kpi.id,
            period=period,
            period_start=start,
            period_end=end,
            estimate_type="historical",
            value=Decimal(value),
            as_of=None,
        )

    def qtd(company: Company, kpi: Kpi, as_of: date, value: str) -> Estimate:
        return Estimate(
            company_id=company.id,
            kpi_id=kpi.id,
            period="2026Q1",
            period_start=date(2026, 1, 1),
            period_end=date(2026, 3, 31),
            estimate_type="qtd",
            value=Decimal(value),
            as_of=as_of,
        )

    # ACME / Total Revenue: three closed quarters of history.
    session.add_all(
        [
            historical(acme, revenue, "2025Q2", date(2025, 4, 1), date(2025, 6, 30), "100"),
            historical(acme, revenue, "2025Q3", date(2025, 7, 1), date(2025, 9, 30), "110"),
            historical(acme, revenue, "2025Q4", date(2025, 10, 1), date(2025, 12, 31), "120"),
        ]
    )
    # ACME / Total Revenue: QTD snapshots, inserted out of as_of order on purpose,
    # so a test can prove the query orders by as_of, not by insertion order.
    session.add_all(
        [
            qtd(acme, revenue, date(2026, 2, 15), "34"),
            qtd(acme, revenue, date(2026, 1, 31), "30"),
            qtd(acme, revenue, date(2026, 3, 15), "40"),
        ]
    )
    # ACME / Units Sold: history only, no QTD (current_qtd must resolve to None).
    session.add_all(
        [
            historical(acme, units, "2025Q3", date(2025, 7, 1), date(2025, 9, 30), "500"),
            historical(acme, units, "2025Q4", date(2025, 10, 1), date(2025, 12, 31), "550"),
        ]
    )
    # GAMM / Total Revenue: a second Cloud company, so a sector search returns two.
    session.add_all(
        [
            historical(gamm, revenue, "2025Q3", date(2025, 7, 1), date(2025, 9, 30), "290"),
            historical(gamm, revenue, "2025Q4", date(2025, 10, 1), date(2025, 12, 31), "300"),
        ]
    )
    # BETA / Total Revenue: a Retail company with both history and QTD.
    session.add_all(
        [
            historical(beta, revenue, "2025Q3", date(2025, 7, 1), date(2025, 9, 30), "200"),
            historical(beta, revenue, "2025Q4", date(2025, 10, 1), date(2025, 12, 31), "210"),
            qtd(beta, revenue, date(2026, 1, 31), "60"),
            qtd(beta, revenue, date(2026, 3, 15), "70"),
        ]
    )


@pytest.fixture(scope="session")
def test_engine() -> Engine:
    """A session-wide engine bound to a freshly built, seeded kpi_test database."""
    url = _test_database_url()
    _ensure_database_exists(url)
    engine = create_engine(url)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        _seed_fixture(session)
        session.commit()
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(test_engine: Engine) -> Session:
    """A session for one test, rolled back at teardown.

    The session is bound to a single connection holding an open transaction.
    Whatever the test writes is discarded when that transaction rolls back, so
    the seeded baseline is identical at the start of every test. autoflush is
    off to match the production SessionLocal, so tests that insert and then
    query must flush explicitly, exactly as production code does.

    join_transaction_mode="create_savepoint" makes the session work inside a
    SAVEPOINT: an application-level commit (the POST /estimates route does one)
    only releases that savepoint, so the outer transaction below still rolls
    back at teardown and API tests stay isolated.
    """
    connection = test_engine.connect()
    transaction = connection.begin()
    session = Session(
        bind=connection,
        autoflush=False,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(db_session: Session) -> TestClient:
    """A TestClient whose routes use the test-bound session.

    get_session is overridden so the API runs against kpi_test and shares this
    test's rolled-back transaction: nothing a request writes survives the test.
    """

    def _use_test_session() -> Iterator[Session]:
        yield db_session

    app.dependency_overrides[get_session] = _use_test_session
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def query_counter(test_engine: Engine) -> SimpleNamespace:
    """Count application SQL statements executed on the test engine.

    Used to prove an endpoint runs a constant number of queries rather than one
    per row (an N+1). A test resets `.count` to zero immediately before the call
    it wants to measure, then asserts on the count afterwards.

    SAVEPOINT statements are excluded: the per-test session runs inside a
    savepoint (see db_session), so those are test-harness transaction control,
    not application queries, and counting them would make the N+1 check depend
    on the fixture instead of on the code under test.
    """
    counter = SimpleNamespace(count=0)
    txn_control = ("SAVEPOINT", "RELEASE SAVEPOINT", "ROLLBACK TO SAVEPOINT")

    def _on_execute(conn, cursor, statement, parameters, context, executemany):
        if statement.lstrip().upper().startswith(txn_control):
            return
        counter.count += 1

    event.listen(test_engine, "before_cursor_execute", _on_execute)
    try:
        yield counter
    finally:
        event.remove(test_engine, "before_cursor_execute", _on_execute)
