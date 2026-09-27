"""
Tests for the bundled sample project.
These tests are run by POST /api/v1/verify/{session_id}.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest

from string_helpers import normalise_username, truncate
from processor import PaymentProcessor, validate_amount
from importer import DataImporter


# ---------------------------------------------------------------------------
# string_helpers
# ---------------------------------------------------------------------------


def test_normalise_username_strips_whitespace():
    assert normalise_username("  Alice  ") == "alice"


def test_normalise_username_lowercases():
    assert normalise_username("BOB") == "bob"


def test_truncate_default():
    assert truncate("x" * 100) == "x" * 80


def test_truncate_custom_len():
    assert truncate("hello world", 5) == "hello"


# ---------------------------------------------------------------------------
# processor
# ---------------------------------------------------------------------------


def test_charge_basic():
    p = PaymentProcessor("stripe")
    result = p.charge(10.0)
    assert result["status"] == "ok"
    assert result["amount"] == 10.0


def test_charge_with_currency():
    p = PaymentProcessor("stripe")
    result = p.charge(5.0, "EUR")
    assert result["status"] == "ok"


def test_charge_negative_raises():
    p = PaymentProcessor("stripe")
    with pytest.raises(ValueError):
        p.charge(-1)


def test_charge_zero_raises():
    p = PaymentProcessor("stripe")
    with pytest.raises(ValueError):
        p.charge(0)


def test_validate_amount_valid():
    assert validate_amount(100.0) is True


def test_validate_amount_zero():
    assert validate_amount(0) is False


def test_validate_amount_exceeds_max():
    assert validate_amount(10_001) is False


# ---------------------------------------------------------------------------
# importer
# ---------------------------------------------------------------------------

_CSV = "name,age\nAlice,30\nBob,25\n"


def test_load_returns_records():
    d = DataImporter("test")
    records = d.load(_CSV)
    assert len(records) == 2
    assert records[0]["name"] == "Alice"


def test_validate_ok():
    d = DataImporter("test")
    records = d.load(_CSV)
    assert d.validate(records, ["name", "age"]) is True


def test_validate_missing_field():
    d = DataImporter("test")
    records = d.load(_CSV)
    assert d.validate(records, ["name", "email"]) is False


def test_transform_strips_whitespace():
    d = DataImporter("test")
    records = [{"name": "  Alice  ", "score": 5}]
    result = d.transform(records)
    assert result[0]["name"] == "Alice"
    assert result[0]["score"] == 5
