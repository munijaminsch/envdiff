"""Flatten nested-style env keys (e.g. APP__DB__HOST) into structured dicts."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any


class FlattenError(Exception):
    """Raised when flattening fails."""


@dataclass
class FlattenResult:
    source: str
    separator: str
    flat: Dict[str, str]
    nested: Dict[str, Any] = field(default_factory=dict)

    @property
    def total_keys(self) -> int:
        return len(self.flat)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "separator": self.separator,
            "total_keys": self.total_keys,
            "flat": dict(self.flat),
            "nested": self.nested,
        }


def _set_nested(target: Dict[str, Any], parts: list[str], value: str) -> None:
    """Recursively assign *value* into *target* following *parts* as path segments."""
    for part in parts[:-1]:
        if part not in target or not isinstance(target[part], dict):
            target[part] = {}
        target = target[part]
    target[parts[-1]] = value


def flatten_env(
    env: Dict[str, str],
    *,
    source: str = "",
    separator: str = "__",
) -> FlattenResult:
    """Convert a flat env dict into a FlattenResult with an optional nested view.

    Args:
        env: Mapping of env key -> value.
        source: Label for the origin file / environment.
        separator: Segment delimiter used in key names (default ``__``).

    Returns:
        A :class:`FlattenResult` containing both the original flat mapping and
        the derived nested dict.

    Raises:
        FlattenError: If *separator* is empty.
    """
    if not separator:
        raise FlattenError("separator must be a non-empty string")

    nested: Dict[str, Any] = {}
    for key, value in env.items():
        parts = key.split(separator)
        _set_nested(nested, parts, value)

    return FlattenResult(
        source=source,
        separator=separator,
        flat=dict(env),
        nested=nested,
    )
