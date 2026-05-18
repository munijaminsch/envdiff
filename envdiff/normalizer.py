"""Normalizer: standardize .env key/value formatting across environments."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


class NormalizeError(Exception):
    """Raised when normalization cannot be performed."""


@dataclass
class NormalizeChange:
    key: str
    original: str
    normalized: str

    def as_dict(self) -> dict:
        return {
            "key": self.key,
            "original": self.original,
            "normalized": self.normalized,
        }


@dataclass
class NormalizeResult:
    source: str
    env: Dict[str, str]
    changes: List[NormalizeChange] = field(default_factory=list)

    @property
    def change_count(self) -> int:
        return len(self.changes)

    @property
    def is_clean(self) -> bool:
        return len(self.changes) == 0

    def as_dict(self) -> dict:
        return {
            "source": self.source,
            "change_count": self.change_count,
            "is_clean": self.is_clean,
            "changes": [c.as_dict() for c in self.changes],
            "env": self.env,
        }


def normalize_env(
    env: Dict[str, str],
    source: str = "<unknown>",
    uppercase_keys: bool = True,
    strip_values: bool = True,
    replace_spaces_in_keys: bool = True,
) -> NormalizeResult:
    """Return a NormalizeResult with standardised keys and values.

    Args:
        env: Parsed key/value mapping.
        source: Label for the origin file (used in result metadata).
        uppercase_keys: Convert all keys to UPPER_CASE.
        strip_values: Strip leading/trailing whitespace from values.
        replace_spaces_in_keys: Replace spaces in keys with underscores.
    """
    if env is None:
        raise NormalizeError("env mapping must not be None")

    normalized: Dict[str, str] = {}
    changes: List[NormalizeChange] = []

    for raw_key, raw_value in env.items():
        new_key = raw_key
        new_value = raw_value

        if replace_spaces_in_keys:
            new_key = new_key.replace(" ", "_")
        if uppercase_keys:
            new_key = new_key.upper()
        if strip_values:
            new_value = new_value.strip()

        if new_key != raw_key or new_value != raw_value:
            changes.append(
                NormalizeChange(
                    key=new_key,
                    original=f"{raw_key}={raw_value}",
                    normalized=f"{new_key}={new_value}",
                )
            )

        normalized[new_key] = new_value

    return NormalizeResult(source=source, env=normalized, changes=changes)
