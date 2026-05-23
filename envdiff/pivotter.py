"""Pivot an env mapping into a grouped-by-value structure.

Given a dict of key→value pairs, build an inverted index where each
unique value maps to the list of keys that share it.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


class PivotError(Exception):
    """Raised when pivoting fails."""


@dataclass
class PivotEntry:
    value: str
    keys: List[str]

    def as_dict(self) -> dict:
        return {"value": self.value, "keys": sorted(self.keys)}


@dataclass
class PivotResult:
    source: str
    entries: List[PivotEntry]

    @property
    def total_values(self) -> int:
        return len(self.entries)

    @property
    def total_keys(self) -> int:
        return sum(len(e.keys) for e in self.entries)

    @property
    def shared_entries(self) -> List[PivotEntry]:
        """Entries where more than one key shares the same value."""
        return [e for e in self.entries if len(e.keys) > 1]

    @property
    def is_clean(self) -> bool:
        """True when no value is shared by multiple keys."""
        return len(self.shared_entries) == 0

    def as_dict(self) -> dict:
        return {
            "source": self.source,
            "total_values": self.total_values,
            "total_keys": self.total_keys,
            "is_clean": self.is_clean,
            "entries": [e.as_dict() for e in self.entries],
        }


def pivot_env(
    env: Dict[str, str],
    source: str = "",
    *,
    ignore_empty: bool = False,
) -> PivotResult:
    """Pivot *env* so that values become keys and keys become lists.

    Args:
        env: Mapping of environment variable names to their values.
        source: Optional label (e.g. filename) stored on the result.
        ignore_empty: When *True*, keys with empty string values are excluded.

    Returns:
        A :class:`PivotResult` instance.

    Raises:
        PivotError: If *env* is not a dict.
    """
    if not isinstance(env, dict):
        raise PivotError(f"env must be a dict, got {type(env).__name__}")

    index: Dict[str, List[str]] = {}
    for key, value in env.items():
        if ignore_empty and value == "":
            continue
        index.setdefault(value, []).append(key)

    entries = [
        PivotEntry(value=v, keys=ks)
        for v, ks in sorted(index.items())
    ]
    return PivotResult(source=source, entries=entries)
