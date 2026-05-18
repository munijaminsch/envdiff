"""Split a flat env dict into multiple env dicts based on key prefixes."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


class SplitError(Exception):
    """Raised when splitting fails."""


@dataclass
class SplitResult:
    source: str
    separator: str
    buckets: Dict[str, Dict[str, str]] = field(default_factory=dict)
    unmatched: Dict[str, str] = field(default_factory=dict)

    @property
    def bucket_names(self) -> List[str]:
        return sorted(self.buckets.keys())

    @property
    def total_keys(self) -> int:
        total = sum(len(v) for v in self.buckets.values())
        return total + len(self.unmatched)

    def as_dict(self) -> dict:
        return {
            "source": self.source,
            "separator": self.separator,
            "buckets": {k: dict(v) for k, v in self.buckets.items()},
            "unmatched": dict(self.unmatched),
            "total_keys": self.total_keys,
        }


def split_by_prefix(
    env: Dict[str, str],
    prefixes: List[str],
    *,
    separator: str = "_",
    strip_prefix: bool = True,
    source: str = "",
) -> SplitResult:
    """Split *env* into buckets keyed by prefix.

    Keys that do not match any prefix land in ``unmatched``.
    """
    if not isinstance(env, dict):
        raise SplitError("env must be a dict")
    if not separator:
        raise SplitError("separator must be a non-empty string")

    buckets: Dict[str, Dict[str, str]] = {p: {} for p in prefixes}
    unmatched: Dict[str, str] = {}

    for key, value in env.items():
        matched = False
        for prefix in prefixes:
            needle = prefix + separator
            if key.startswith(needle):
                bucket_key = key[len(needle):] if strip_prefix else key
                buckets[prefix][bucket_key] = value
                matched = True
                break
        if not matched:
            unmatched[key] = value

    return SplitResult(
        source=source,
        separator=separator,
        buckets=buckets,
        unmatched=unmatched,
    )
