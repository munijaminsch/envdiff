"""Tests for envdiff.renamer."""
import pytest

from envdiff.renamer import RenameError, RenameResult, rename_keys


def _env(**kwargs: str) -> dict:
    return dict(kwargs)


# ---------------------------------------------------------------------------
# RenameResult helpers
# ---------------------------------------------------------------------------

def test_rename_result_applied_count():
    r = RenameResult(original={}, renamed={}, applied=[("A", "B")], skipped=[])
    assert r.applied_count == 1


def test_rename_result_skipped_count():
    r = RenameResult(original={}, renamed={}, applied=[], skipped=[("X", "Y"), ("Z", "W")])
    assert r.skipped_count == 2


def test_rename_result_as_dict_keys():
    r = RenameResult(original={}, renamed={"B": "1"}, applied=[("A", "B")], skipped=[])
    d = r.as_dict()
    assert set(d.keys()) == {"renamed", "applied", "skipped", "applied_count", "skipped_count"}


# ---------------------------------------------------------------------------
# rename_keys — happy path
# ---------------------------------------------------------------------------

def test_simple_rename():
    env = _env(OLD_KEY="value")
    result = rename_keys(env, {"OLD_KEY": "NEW_KEY"})
    assert "NEW_KEY" in result.renamed
    assert "OLD_KEY" not in result.renamed
    assert result.renamed["NEW_KEY"] == "value"


def test_applied_records_rename():
    env = _env(FOO="bar")
    result = rename_keys(env, {"FOO": "BAZ"})
    assert ("FOO", "BAZ") in result.applied


def test_multiple_renames():
    env = _env(A="1", B="2", C="3")
    result = rename_keys(env, {"A": "X", "B": "Y"})
    assert result.renamed == {"X": "1", "Y": "2", "C": "3"}
    assert result.applied_count == 2


def test_original_is_not_mutated():
    env = _env(KEY="val")
    rename_keys(env, {"KEY": "NEW"})
    assert "KEY" in env  # original dict unchanged


# ---------------------------------------------------------------------------
# rename_keys — skipping
# ---------------------------------------------------------------------------

def test_skips_missing_source_key():
    env = _env(A="1")
    result = rename_keys(env, {"MISSING": "NEW"})
    assert ("MISSING", "NEW") in result.skipped
    assert result.applied_count == 0


def test_skips_when_target_exists_no_overwrite():
    env = _env(OLD="1", NEW="existing")
    result = rename_keys(env, {"OLD": "NEW"}, overwrite=False)
    assert ("OLD", "NEW") in result.skipped
    assert result.renamed["OLD"] == "1"  # old key preserved
    assert result.renamed["NEW"] == "existing"  # existing value preserved


def test_overwrites_when_flag_set():
    env = _env(OLD="new_val", NEW="old_val")
    result = rename_keys(env, {"OLD": "NEW"}, overwrite=True)
    assert result.renamed["NEW"] == "new_val"
    assert "OLD" not in result.renamed
    assert result.applied_count == 1


# ---------------------------------------------------------------------------
# rename_keys — error handling
# ---------------------------------------------------------------------------

def test_raises_on_duplicate_targets():
    env = _env(A="1", B="2")
    with pytest.raises(RenameError, match="duplicate"):
        rename_keys(env, {"A": "C", "B": "C"})


def test_empty_mapping_returns_unchanged_env():
    env = _env(FOO="bar", BAZ="qux")
    result = rename_keys(env, {})
    assert result.renamed == env
    assert result.applied_count == 0
    assert result.skipped_count == 0
