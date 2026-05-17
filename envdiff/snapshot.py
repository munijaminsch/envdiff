"""Snapshot: capture and compare env state at a point in time."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional


class SnapshotError(Exception):
    """Raised when a snapshot operation fails."""


@dataclass
class EnvSnapshot:
    """Represents a captured snapshot of an env file."""

    source: str
    keys: Dict[str, str] = field(default_factory=dict)
    timestamp: Optional[str] = None

    @property
    def key_count(self) -> int:
        return len(self.keys)

    def as_dict(self) -> dict:
        return {
            "source": self.source,
            "timestamp": self.timestamp,
            "key_count": self.key_count,
            "keys": dict(self.keys),
        }


@dataclass
class SnapshotDiff:
    """Difference between two snapshots."""

    added: Dict[str, str] = field(default_factory=dict)
    removed: Dict[str, str] = field(default_factory=dict)
    changed: Dict[str, tuple] = field(default_factory=dict)

    @property
    def is_clean(self) -> bool:
        return not (self.added or self.removed or self.changed)

    def as_dict(self) -> dict:
        return {
            "added": dict(self.added),
            "removed": dict(self.removed),
            "changed": {k: {"before": v[0], "after": v[1]} for k, v in self.changed.items()},
            "is_clean": self.is_clean,
        }


def take_snapshot(env: Dict[str, str], source: str, timestamp: Optional[str] = None) -> EnvSnapshot:
    """Create a snapshot from a parsed env dict."""
    return EnvSnapshot(source=source, keys=dict(env), timestamp=timestamp)


def save_snapshot(snapshot: EnvSnapshot, path: Path) -> None:
    """Persist a snapshot to a JSON file."""
    try:
        path.write_text(json.dumps(snapshot.as_dict(), indent=2))
    except OSError as exc:
        raise SnapshotError(f"Cannot write snapshot to {path}: {exc}") from exc


def load_snapshot(path: Path) -> EnvSnapshot:
    """Load a snapshot from a JSON file."""
    if not path.exists():
        raise SnapshotError(f"Snapshot file not found: {path}")
    try:
        data = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError) as exc:
        raise SnapshotError(f"Cannot read snapshot from {path}: {exc}") from exc
    return EnvSnapshot(
        source=data.get("source", ""),
        keys=data.get("keys", {}),
        timestamp=data.get("timestamp"),
    )


def diff_snapshots(before: EnvSnapshot, after: EnvSnapshot) -> SnapshotDiff:
    """Compute the difference between two snapshots."""
    before_keys = before.keys
    after_keys = after.keys
    added = {k: v for k, v in after_keys.items() if k not in before_keys}
    removed = {k: v for k, v in before_keys.items() if k not in after_keys}
    changed = {
        k: (before_keys[k], after_keys[k])
        for k in before_keys
        if k in after_keys and before_keys[k] != after_keys[k]
    }
    return SnapshotDiff(added=added, removed=removed, changed=changed)
