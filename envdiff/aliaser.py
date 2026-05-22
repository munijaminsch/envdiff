"""aliaser.py — Map env keys to aliases and produce a renamed view."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


class AliasError(Exception):
    """Raised when aliasing fails."""


@dataclass
class AliasedKey:
    original: str
    alias: str
    value: str

    def as_dict(self) -> dict:
        return {"original": self.original, "alias": self.alias, "value": self.value}


@dataclass
class AliasResult:
    source: str
    entries: List[AliasedKey] = field(default_factory=list)
    unmapped: List[str] = field(default_factory=list)

    @property
    def total_keys(self) -> int:
        return len(self.entries) + len(self.unmapped)

    @property
    def mapped_count(self) -> int:
        return len(self.entries)

    @property
    def unmapped_count(self) -> int:
        return len(self.unmapped)

    @property
    def is_clean(self) -> bool:
        """True when every key has an alias."""
        return len(self.unmapped) == 0

    def as_dict(self) -> dict:
        return {
            "source": self.source,
            "mapped": [e.as_dict() for e in self.entries],
            "unmapped": list(self.unmapped),
            "mapped_count": self.mapped_count,
            "unmapped_count": self.unmapped_count,
        }


def apply_aliases(
    env: Dict[str, str],
    mapping: Dict[str, str],
    *,
    source: str = "<env>",
    strict: bool = False,
) -> AliasResult:
    """Apply *mapping* (original -> alias) to *env*.

    Parameters
    ----------
    env:
        Parsed key/value pairs.
    mapping:
        Dict mapping original key names to desired alias names.
    source:
        Label used for reporting (e.g. file path).
    strict:
        If True, raise :class:`AliasError` when any key has no alias.
    """
    if mapping is None:
        raise AliasError("mapping must not be None")

    entries: List[AliasedKey] = []
    unmapped: List[str] = []

    for key, value in env.items():
        if key in mapping:
            entries.append(AliasedKey(original=key, alias=mapping[key], value=value))
        else:
            unmapped.append(key)

    if strict and unmapped:
        raise AliasError(
            f"strict mode: {len(unmapped)} key(s) have no alias: {unmapped}"
        )

    return AliasResult(source=source, entries=entries, unmapped=unmapped)
