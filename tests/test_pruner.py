"""Tests for envdiff.pruner."""

import pytest

from envdiff.pruner import PruneError, PruneResult, PrunedKey, prune


def _env(**kwargs: str) -> dict:
    return dict(kwargs)


# ---------------------------------------------------------------------------
# PruneResult helpers
# ---------------------------------------------------------------------------

def test_returns_prune_result():
    result = prune(_env(A="1"), allowed_keys=["A"])
    assert isinstance(result, PruneResult)


def test_source_stored():
    result = prune(_env(A="1"), allowed_keys=["A"], source="prod.env")
    assert result.source == "prod.env"


def test_default_source():
    result = prune(_env(A="1"), allowed_keys=["A"])
    assert result.source == "<env>"


def test_is_clean_when_nothing_removed():
    result = prune(_env(A="1", B="2"), allowed_keys=["A", "B"])
    assert result.is_clean


def test_not_clean_when_keys_removed():
    result = prune(_env(A="1", B="2"), allowed_keys=["A"])
    assert not result.is_clean


def test_removed_count():
    result = prune(_env(A="1", B="2", C="3"), allowed_keys=["A"])
    assert result.removed_count == 2


def test_kept_count():
    result = prune(_env(A="1", B="2", C="3"), allowed_keys=["A", "C"])
    assert result.kept_count == 2


# ---------------------------------------------------------------------------
# allowed_keys
# ---------------------------------------------------------------------------

def test_allowed_key_not_removed():
    result = prune(_env(KEEP="yes", DROP="no"), allowed_keys=["KEEP"])
    entry = next(e for e in result.entries if e.key == "KEEP")
    assert not entry.removed


def test_disallowed_key_removed():
    result = prune(_env(KEEP="yes", DROP="no"), allowed_keys=["KEEP"])
    entry = next(e for e in result.entries if e.key == "DROP")
    assert entry.removed


def test_empty_allowed_keys_removes_all():
    result = prune(_env(A="1", B="2"), allowed_keys=[], allowed_patterns=[])
    assert result.removed_count == 2


# ---------------------------------------------------------------------------
# allowed_patterns
# ---------------------------------------------------------------------------

def test_pattern_keeps_matching_key():
    result = prune(_env(APP_HOST="localhost", SECRET="x"), allowed_patterns=[r"^APP_"])
    kept = [e for e in result.entries if not e.removed]
    assert len(kept) == 1
    assert kept[0].key == "APP_HOST"


def test_pattern_and_key_union():
    result = prune(
        _env(APP_HOST="h", DB_URL="u", SECRET="s"),
        allowed_keys=["DB_URL"],
        allowed_patterns=[r"^APP_"],
    )
    assert result.kept_count == 2
    assert result.removed_count == 1


def test_invalid_pattern_raises():
    with pytest.raises(PruneError, match="Invalid pattern"):
        prune(_env(A="1"), allowed_patterns=["[invalid"])


# ---------------------------------------------------------------------------
# No criteria raises
# ---------------------------------------------------------------------------

def test_no_criteria_raises():
    with pytest.raises(PruneError):
        prune(_env(A="1"))


# ---------------------------------------------------------------------------
# as_dict
# ---------------------------------------------------------------------------

def test_as_dict_structure():
    result = prune(_env(A="1", B="2"), allowed_keys=["A"])
    d = result.as_dict()
    assert d["source"] == "<env>"
    assert d["removed_count"] == 1
    assert d["kept_count"] == 1
    assert isinstance(d["entries"], list)
    assert all("key" in e and "value" in e and "removed" in e for e in d["entries"])


def test_entry_value_preserved():
    result = prune(_env(X="hello"), allowed_keys=["X"])
    assert result.entries[0].value == "hello"
