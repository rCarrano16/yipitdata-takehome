"""SQLAlchemy engine, session factory, and session helpers."""

from collections.abc import Generator, Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings

# pool_pre_ping checks that a pooled connection is still alive before handing it
# out, so a connection dropped by the database does not surface as a query error.
engine = create_engine(settings.database_url, pool_pre_ping=True)

# autoflush is off for explicit control: nothing reaches the database until an
# explicit flush() or commit(). expire_on_commit is off so ORM attributes stay
# readable after the transaction commits.
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency: yield a session, rolling back on error, then closing.

    The rollback is symmetric with session_scope: a request that fails must not
    leave a half-finished transaction on the pooled connection for the next
    request to inherit.
    """
    session = SessionLocal()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@contextmanager
def session_scope() -> Iterator[Session]:
    """Session context manager: commit on success, roll back on error, always close."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@contextmanager
def read_only_session() -> Iterator[Session]:
    """Session context manager for reads: roll back on exit, never commit.

    The MCP server uses this for every tool. Rolling back instead of committing
    discards any state and ends the transaction cleanly, so the read-only MCP
    server is read-only by construction, not only by convention.
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
