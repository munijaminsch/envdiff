"""Removes duplicate keys from an env mapping, keeping the last occurrence."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple


class DeduplicateError(Exception):
    """Raised when deduplication cannot be performed."""


@dataclass
class RemovedEntry:
    key: str
    kept_value: str
    dropped_values: List[str]

    def as_dict(self) -> dict:
        return {
            "key": self.key,
            "kept_value": self.kept_value,
            "dropped_values": self.dropped_values,
        }


@dataclass
class DeduplicateResult:
    source: str
    env: Dict[str, str]
    removed: List[RemovedEntry] = field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        return len(self.removed) == 0

    @property
    def removed_count(self) -> int:
        return len(self.removed)

    def as_dict(self) -> dict:
        return {
            "source": self.source,
            "is_clean": self.is_clean,
            "removed_count": self.removed_count,
            "removed": [r.as_dict() for r in self.removed],
            "env": self.env,
        }


def deduplicate(
    pairs: List[Tuple[str, str]],
    source: str = "<unknown>",
) -> DeduplicateResult:
    """Given an ordered list of (key, value) pairs (possibly with repeated keys),
    return a DeduplicateResult that keeps the *last* value for each key and
    records which earlier values were dropped.

    Args:
        pairs: Ordered sequence of (key, value) tuples as produced by a raw
               parser that does not deduplicate on its own.
        source: Label for the originating file.

    Returns:
        DeduplicateResult with the clean env dict and metadata about removals.

    Raises:
        DeduplicateError: If *pairs* is not iterable or contains non-string items.
    """
    if pairs is None:
        raise DeduplicateError("pairs must not be None")

    # Collect all values per key in order
    seen: Dict[str, List[str]] = {}
    try:
        for key, value in pairs:
            if not isinstance(key, str) or not isinstance(value, str):
                raise DeduplicateError(
                    f"All keys and values must be strings, got {key!r}: {value!r}"
                )
            seen.setdefault(key, []).append(value)
    except TypeError as exc:
        raise DeduplicateError(f"pairs must be iterable of (str, str): {exc}") from exc

    env: Dict[str, str] = {}
    removed: List[RemovedEntry] = []

    for key, values in seen.items():
        env[key] = values[-1]
        if len(values) > 1:
            removed.append(
                RemovedEntry(
                    key=key,
                    kept_value=values[-1],
                    dropped_values=values[:-1],
                )
            )

    return DeduplicateResult(source=source, env=env, removed=removed)
