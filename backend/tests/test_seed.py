"""Tests for the CSV seed's per-row validation.

`_parse_row` is a pure function: it validates one CSV row (all strings, as the
csv.DictReader yields it) and returns native Python types, or raises ValueError.
These tests cover the qtd as_of / period-window rule, which mirrors the
PublishEstimateRequest schema, and need no database.
"""

import pytest

from app.seed import _parse_row


def _qtd_row(**overrides) -> dict:
    """A valid qtd CSV row as csv.DictReader would yield it (every value a str)."""
    row = {
        "company_name": "Acme E-commerce",
        "ticker": "ACME",
        "sector": "E-commerce",
        "kpi": "ASP ($)",
        "period_start": "2026-01-01",
        "period_end": "2026-03-31",
        "period": "2026Q1",
        "estimate_type": "qtd",
        "value": "162.95",
        "unit": "$",
        "as_of": "2026-01-31",
    }
    row.update(overrides)
    return row


def test_parse_row_accepts_a_qtd_as_of_inside_the_window():
    parsed = _parse_row(_qtd_row(), line_no=2)
    assert parsed["as_of"].isoformat() == "2026-01-31"


def test_parse_row_rejects_a_qtd_as_of_after_the_period_window():
    with pytest.raises(ValueError, match="outside the period window"):
        _parse_row(_qtd_row(as_of="2026-04-01"), line_no=2)


def test_parse_row_rejects_a_qtd_as_of_before_the_period_window():
    with pytest.raises(ValueError, match="outside the period window"):
        _parse_row(_qtd_row(as_of="2025-12-31"), line_no=2)


def test_parse_row_rejects_a_malformed_period():
    # period must be a quarter code like 2026Q1, the same rule the publish
    # endpoint enforces, so a CSV-formula string cannot reach the stored data.
    with pytest.raises(ValueError, match="invalid period"):
        _parse_row(_qtd_row(period="=1+1"), line_no=2)
