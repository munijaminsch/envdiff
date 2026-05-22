"""Prune keys from an env mapping based on a set of allowed keys or patterns."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


class PruneError(Exception):
    """Raised when pruning cannot be completed."""


@dataclass
class PrunedKey:
    key: str
    value: str
    removed: bool

    def as_dict(self) -> dict:
        return {"key": self.key, "value": self.value, "removed": self.removed}


@dataclass
class PruneResult:
    source: str
    entries: List[PrunedKey] = field(default_factory=list)

    @property
    def removed_count(self) -> int:
        return sum(1 for e in self.entries if e.removed)

    @property
    def kept_count(self) -> int:
        return sum(1 for e in self.entries if not e.removed)

    @property
    def is_clean(self) -> bool:
        return self.removed_count == 0

    def as_dict(self) -> dict:
        return {
            "source": self.source,
            "removed_count": self.removed_count,
            "kept_count": self.kept_count,
            "entries": [e.as_dict() for e in self.entries],
        }


def _compile_patterns(patterns: List[str]) -> List[re.Pattern]:
    try:
        return [re.compile(p) for p in patterns]
    except re.error as exc:
        raise PruneError(f"Invalid pattern: {exc}") from exc


def prune(
    env: Dict[str, str],
    *,
    allowed_keys: Optional[List[str]] = None,
    allowed_patterns: Optional[List[str]] = None,
    source: str = "<env>",
) -> PruneResult:
    """Remove keys not in *allowed_keys* or matching *allowed_patterns*."""
    if allowed_keys is None and allowed_patterns is None:
        raise PruneError("At least one of allowed_keys or allowed_patterns must be provided.")

    key_set = set(allowed_keys or [])
    compiled = _compile_patterns(allowed_patterns or [])

    result = PruneResult(source=source)
    for key, value in env.items():
        keep = key in key_set or any(p.search(key) for p in compiled)
        result.entries.append(PrunedKey(key=key, value=value, removed=not keep))

    return result
