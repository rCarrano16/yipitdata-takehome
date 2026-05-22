"""Fixtures for the MCP server tests.

The seven MCP tools are tested in isolation from any database. Each tool's job
is the MCP-specific glue: open a session, call one backend service function,
and shape the result (or translate a NotFoundError into a ToolError). The
service layer's own database behavior is already covered by the backend test
suite, so here it is stubbed per test. `read_only_session` is replaced with a
no-op context manager, so no MCP test opens a database connection: the suite is
fully deterministic and independent of the development database (it passes even
with Postgres stopped). The two prompts are pure string templates and need no
stub.
"""

from collections.abc import Iterator
from contextlib import contextmanager

import pytest

import server


@contextmanager
def _no_db_session() -> Iterator[None]:
    """Stand in for app.db.read_only_session without opening a database connection.

    The backend service functions are stubbed in every test, so the session they
    would receive is never used; yielding None is enough.
    """
    yield None


@pytest.fixture(autouse=True)
def stub_read_only_session(monkeypatch: pytest.MonkeyPatch) -> None:
    """Point every tool's read_only_session at the no-op session, so no test hits a DB."""
    monkeypatch.setattr(server, "read_only_session", _no_db_session)
