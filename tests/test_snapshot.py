"""Tests for envdiff.snapshot."""
import json
import pytest
from pathlib import Path

from envdiff.snapshot import (
    EnvSnapshot,
    SnapshotDiff,
    SnapshotError,
    take_snapshot,
    save_snapshot,
    load_snapshot,
    diff_snapshots,
)


def _env(**kwargs) -> dict:
    return {k: v for k, v in kwargs.items()}


# --- take_snapshot ---

def test_take_snapshot_returns_env_snapshot():
    snap = take_snapshot({"A": "1"}, source=".env")
    assert isinstance(snap, EnvSnapshot)


def test_take_snapshot_stores_source():
    snap = take_snapshot({}, source="prod.env")
    assert snap.source == "prod.env"


def test_take_snapshot_stores_keys():
    snap = take_snapshot({"FOO": "bar", "BAZ": "qux"}, source=".env")
    assert snap.keys == {"FOO": "bar", "BAZ": "qux"}


def test_take_snapshot_key_count():
    snap = take_snapshot({"A": "1", "B": "2", "C": "3"}, source=".env")
    assert snap.key_count == 3


def test_take_snapshot_stores_timestamp():
    snap = take_snapshot({}, source=".env", timestamp="2024-01-01T00:00:00")
    assert snap.timestamp == "2024-01-01T00:00:00"


def test_take_snapshot_timestamp_defaults_none():
    snap = take_snapshot({}, source=".env")
    assert snap.timestamp is None


# --- as_dict ---

def test_as_dict_contains_expected_keys():
    snap = take_snapshot({"X": "y"}, source="test.env", timestamp="ts")
    d = snap.as_dict()
    assert set(d.keys()) == {"source", "timestamp", "key_count", "keys"}


def test_as_dict_key_count_matches():
    snap = take_snapshot({"A": "1", "B": "2"}, source=".env")
    assert snap.as_dict()["key_count"] == 2


# --- save / load ---

def test_save_and_load_round_trip(tmp_path):
    snap = take_snapshot({"DB": "postgres"}, source="dev.env", timestamp="now")
    out = tmp_path / "snap.json"
    save_snapshot(snap, out)
    loaded = load_snapshot(out)
    assert loaded.source == snap.source
    assert loaded.keys == snap.keys
    assert loaded.timestamp == snap.timestamp


def test_load_raises_for_missing_file(tmp_path):
    with pytest.raises(SnapshotError, match="not found"):
        load_snapshot(tmp_path / "missing.json")


def test_save_raises_for_bad_path():
    bad = Path("/nonexistent_dir/snap.json")
    snap = take_snapshot({}, source=".env")
    with pytest.raises(SnapshotError):
        save_snapshot(snap, bad)


def test_load_raises_for_invalid_json(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("not json {{{")
    with pytest.raises(SnapshotError):
        load_snapshot(bad)


# --- diff_snapshots ---

def test_diff_snapshots_returns_snapshot_diff():
    a = take_snapshot({"A": "1"}, source="a")
    b = take_snapshot({"A": "1"}, source="b")
    assert isinstance(diff_snapshots(a, b), SnapshotDiff)


def test_diff_is_clean_for_identical_snapshots():
    a = take_snapshot({"A": "1", "B": "2"}, source="a")
    b = take_snapshot({"A": "1", "B": "2"}, source="b")
    assert diff_snapshots(a, b).is_clean


def test_diff_detects_added_key():
    a = take_snapshot({"A": "1"}, source="a")
    b = take_snapshot({"A": "1", "NEW": "val"}, source="b")
    diff = diff_snapshots(a, b)
    assert "NEW" in diff.added


def test_diff_detects_removed_key():
    a = take_snapshot({"A": "1", "OLD": "gone"}, source="a")
    b = take_snapshot({"A": "1"}, source="b")
    diff = diff_snapshots(a, b)
    assert "OLD" in diff.removed


def test_diff_detects_changed_value():
    a = take_snapshot({"PORT": "3000"}, source="a")
    b = take_snapshot({"PORT": "8080"}, source="b")
    diff = diff_snapshots(a, b)
    assert "PORT" in diff.changed
    assert diff.changed["PORT"] == ("3000", "8080")


def test_diff_as_dict_structure():
    a = take_snapshot({"A": "old"}, source="a")
    b = take_snapshot({"A": "new", "B": "added"}, source="b")
    d = diff_snapshots(a, b).as_dict()
    assert "added" in d and "removed" in d and "changed" in d and "is_clean" in d


def test_diff_changed_as_dict_has_before_after():
    a = take_snapshot({"X": "1"}, source="a")
    b = take_snapshot({"X": "2"}, source="b")
    d = diff_snapshots(a, b).as_dict()
    assert d["changed"]["X"] == {"before": "1", "after": "2"}
