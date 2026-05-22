"""Pin env keys to expected values and detect drift."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


class PinError(Exception):
    """Raised when pinning operations fail."""


@dataclass
class PinnedKey:
    key: str
    expected: str
    actual: Optional[str]
    is_pinned: bool  # True when actual matches expected
    is_missing: bool  # True when key absent from env

    def as_dict(self) -> dict:
        return {
            "key": self.key,
            "expected": self.expected,
            "actual": self.actual,
            "is_pinned": self.is_pinned,
            "is_missing": self.is_missing,
        }


@dataclass
class PinResult:
    source: str
    entries: List[PinnedKey] = field(default_factory=list)

    @property
    def total_keys(self) -> int:
        return len(self.entries)

    @property
    def drift_count(self) -> int:
        return sum(1 for e in self.entries if not e.is_pinned)

    @property
    def is_clean(self) -> bool:
        return self.drift_count == 0

    def as_dict(self) -> dict:
        return {
            "source": self.source,
            "total_keys": self.total_keys,
            "drift_count": self.drift_count,
            "is_clean": self.is_clean,
            "entries": [e.as_dict() for e in self.entries],
        }


def pin_env(
    env: Dict[str, str],
    pins: Dict[str, str],
    source: str = "<env>",
) -> PinResult:
    """Compare *env* against *pins* (expected key→value map).

    Args:
        env:    Parsed environment dictionary.
        pins:   Mapping of key → expected value.
        source: Label for the environment being checked.

    Returns:
        A :class:`PinResult` describing which keys match, drift, or are missing.

    Raises:
        PinError: If *pins* is empty.
    """
    if not pins:
        raise PinError("pins mapping must not be empty")

    entries: List[PinnedKey] = []
    for key, expected in pins.items():
        actual = env.get(key)
        is_missing = actual is None
        is_pinned = not is_missing and actual == expected
        entries.append(
            PinnedKey(
                key=key,
                expected=expected,
                actual=actual,
                is_pinned=is_pinned,
                is_missing=is_missing,
            )
        )

    return PinResult(source=source, entries=entries)
