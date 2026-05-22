"""Tests for envdiff.pinner."""
import pytest

from envdiff.pinner import PinError, PinnedKey, PinResult, pin_env


def _env(**kwargs: str) -> dict:
    return dict(kwargs)


# ---------------------------------------------------------------------------
# pin_env return type
# ---------------------------------------------------------------------------

def test_returns_pin_result():
    result = pin_env(_env(KEY="val"), {"KEY": "val"})
    assert isinstance(result, PinResult)


def test_source_stored():
    result = pin_env(_env(KEY="val"), {"KEY": "val"}, source="prod.env")
    assert result.source == "prod.env"


def test_default_source():
    result = pin_env(_env(KEY="val"), {"KEY": "val"})
    assert result.source == "<env>"


# ---------------------------------------------------------------------------
# counts
# ---------------------------------------------------------------------------

def test_total_keys_matches_pin_count():
    pins = {"A": "1", "B": "2", "C": "3"}
    result = pin_env(_env(A="1", B="2", C="3"), pins)
    assert result.total_keys == 3


def test_drift_count_zero_when_all_match():
    result = pin_env(_env(X="hello"), {"X": "hello"})
    assert result.drift_count == 0


def test_drift_count_counts_mismatches():
    result = pin_env(_env(A="wrong", B="ok"), {"A": "right", "B": "ok"})
    assert result.drift_count == 1


def test_drift_count_counts_missing_keys():
    result = pin_env(_env(), {"MISSING": "value"})
    assert result.drift_count == 1


# ---------------------------------------------------------------------------
# is_clean
# ---------------------------------------------------------------------------

def test_is_clean_when_no_drift():
    result = pin_env(_env(K="v"), {"K": "v"})
    assert result.is_clean is True


def test_not_clean_when_drift_present():
    result = pin_env(_env(K="wrong"), {"K": "right"})
    assert result.is_clean is False


# ---------------------------------------------------------------------------
# entry-level checks
# ---------------------------------------------------------------------------

def test_matching_key_is_pinned():
    result = pin_env(_env(DB="postgres"), {"DB": "postgres"})
    entry = result.entries[0]
    assert entry.is_pinned is True
    assert entry.is_missing is False


def test_mismatched_key_is_not_pinned():
    result = pin_env(_env(DB="sqlite"), {"DB": "postgres"})
    entry = result.entries[0]
    assert entry.is_pinned is False
    assert entry.is_missing is False
    assert entry.actual == "sqlite"


def test_missing_key_flagged():
    result = pin_env(_env(), {"SECRET": "abc123"})
    entry = result.entries[0]
    assert entry.is_missing is True
    assert entry.is_pinned is False
    assert entry.actual is None


# ---------------------------------------------------------------------------
# as_dict
# ---------------------------------------------------------------------------

def test_as_dict_structure():
    result = pin_env(_env(A="1"), {"A": "1"}, source="test.env")
    d = result.as_dict()
    assert d["source"] == "test.env"
    assert d["is_clean"] is True
    assert d["drift_count"] == 0
    assert isinstance(d["entries"], list)


def test_entry_as_dict_keys():
    result = pin_env(_env(A="1"), {"A": "1"})
    entry_dict = result.entries[0].as_dict()
    assert set(entry_dict.keys()) == {"key", "expected", "actual", "is_pinned", "is_missing"}


# ---------------------------------------------------------------------------
# error cases
# ---------------------------------------------------------------------------

def test_empty_pins_raises():
    with pytest.raises(PinError, match="empty"):
        pin_env(_env(A="1"), {})
