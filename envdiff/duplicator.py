"""Detect duplicate values across keys in an env mapping."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


class DuplicateError(Exception):
    """Raised when duplicate detection fails."""


@dataclass
class DuplicateGroup:
    """A set of keys that share the same value."""

    value: str
    keys: List[str]

    def as_dict(self) -> dict:
        return {"value": self.value, "keys": sorted(self.keys)}


@dataclass
class DuplicateResult:
    """Result of a duplicate-value scan over a single env mapping."""

    source: str
    groups: List[DuplicateGroup] = field(default_factory=list)

    @property
    def total_keys(self) -> int:
        return sum(len(g.keys) for g in self.groups)

    @property
    def is_clean(self) -> bool:
        return len(self.groups) == 0

    def as_dict(self) -> dict:
        return {
            "source": self.source,
            "is_clean": self.is_clean,
            "duplicate_groups": [g.as_dict() for g in self.groups],
        }


def find_duplicates(
    env: Dict[str, str],
    source: str = "",
    ignore_empty: bool = False,
) -> DuplicateResult:
    """Return a DuplicateResult listing keys that share identical values.

    Parameters
    ----------
    env:
        Mapping of key -> value (e.g. from parse_env_file).
    source:
        Label for the origin file (stored in the result).
    ignore_empty:
        When *True*, keys with an empty string value are excluded from
        duplicate detection (empty values are common and usually intentional).
    """
    if env is None:
        raise DuplicateError("env mapping must not be None")

    value_to_keys: Dict[str, List[str]] = {}
    for key, value in env.items():
        if ignore_empty and value == "":
            continue
        value_to_keys.setdefault(value, []).append(key)

    groups = [
        DuplicateGroup(value=val, keys=keys)
        for val, keys in value_to_keys.items()
        if len(keys) > 1
    ]
    groups.sort(key=lambda g: g.value)

    return DuplicateResult(source=source, groups=groups)
