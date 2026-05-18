"""Strip unused or orphaned keys from an env file based on a reference template."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


class StripError(Exception):
    """Raised when stripping fails."""


@dataclass
class StrippedKey:
    key: str
    value: str

    def as_dict(self) -> dict:
        return {"key": self.key, "value": self.value}


@dataclass
class StripResult:
    source: str
    reference: str
    kept: Dict[str, str] = field(default_factory=dict)
    removed: List[StrippedKey] = field(default_factory=list)

    @property
    def removed_count(self) -> int:
        return len(self.removed)

    @property
    def is_clean(self) -> bool:
        return self.removed_count == 0

    def as_dict(self) -> dict:
        return {
            "source": self.source,
            "reference": self.reference,
            "kept": dict(self.kept),
            "removed": [r.as_dict() for r in self.removed],
            "removed_count": self.removed_count,
            "is_clean": self.is_clean,
        }


def strip_keys(
    env: Dict[str, str],
    reference: Dict[str, str],
    source: str = "<source>",
    reference_name: str = "<reference>",
) -> StripResult:
    """Remove keys from *env* that are not present in *reference*.

    Args:
        env: The environment dict to strip.
        reference: The reference dict whose keys define what is allowed.
        source: Label for the source env (used in result metadata).
        reference_name: Label for the reference env.

    Returns:
        A :class:`StripResult` containing kept keys and removed keys.
    """
    if env is None:
        raise StripError("env must not be None")
    if reference is None:
        raise StripError("reference must not be None")

    ref_keys = set(reference.keys())
    kept: Dict[str, str] = {}
    removed: List[StrippedKey] = []

    for key, value in env.items():
        if key in ref_keys:
            kept[key] = value
        else:
            removed.append(StrippedKey(key=key, value=value))

    removed.sort(key=lambda k: k.key)

    return StripResult(
        source=source,
        reference=reference_name,
        kept=kept,
        removed=removed,
    )
