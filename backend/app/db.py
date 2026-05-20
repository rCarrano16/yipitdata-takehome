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
    """FastAPI dependency: yield a session and close it when the request ends."""
    session = SessionLocal()
    try:
        yield session
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
