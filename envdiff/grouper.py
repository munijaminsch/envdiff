"""Groups env keys by prefix (e.g. DB_, AWS_, APP_) for structured reporting."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


class GroupError(Exception):
    """Raised when grouping fails."""


@dataclass
class EnvGroup:
    """A named group of keys sharing a common prefix."""

    prefix: str
    keys: List[str] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.keys)

    def as_dict(self) -> dict:
        return {"prefix": self.prefix, "count": self.count, "keys": sorted(self.keys)}


@dataclass
class GroupResult:
    """Result of grouping an env mapping by prefix."""

    groups: Dict[str, EnvGroup] = field(default_factory=dict)
    ungrouped: List[str] = field(default_factory=list)

    @property
    def group_names(self) -> List[str]:
        return sorted(self.groups.keys())

    @property
    def total_grouped(self) -> int:
        return sum(g.count for g in self.groups.values())

    def as_dict(self) -> dict:
        return {
            "groups": {name: g.as_dict() for name, g in sorted(self.groups.items())},
            "ungrouped": sorted(self.ungrouped),
            "total_grouped": self.total_grouped,
            "ungrouped_count": len(self.ungrouped),
        }


def group_by_prefix(
    env: Dict[str, str],
    sep: str = "_",
    min_prefix_length: int = 1,
    known_prefixes: Optional[List[str]] = None,
) -> GroupResult:
    """Group env keys by their prefix (the part before the first separator).

    Args:
        env: Mapping of key -> value.
        sep: Separator character used to split the prefix from the rest.
        min_prefix_length: Minimum number of characters a prefix must have.
        known_prefixes: If provided, only group keys matching these prefixes;
                        all others go to ``ungrouped``.

    Returns:
        A :class:`GroupResult` instance.
    """
    if not isinstance(env, dict):
        raise GroupError("env must be a dict")
    if not sep:
        raise GroupError("sep must be a non-empty string")

    normalised_known = (
        {p.upper() for p in known_prefixes} if known_prefixes is not None else None
    )

    groups: Dict[str, EnvGroup] = {}
    ungrouped: List[str] = []

    for key in env:
        parts = key.split(sep, 1)
        if len(parts) == 2 and len(parts[0]) >= min_prefix_length:
            prefix = parts[0].upper()
            if normalised_known is None or prefix in normalised_known:
                if prefix not in groups:
                    groups[prefix] = EnvGroup(prefix=prefix)
                groups[prefix].keys.append(key)
                continue
        ungrouped.append(key)

    return GroupResult(groups=groups, ungrouped=ungrouped)
