"""Trimmer: removes leading/trailing whitespace from env values."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


class TrimError(Exception):
    """Raised when trimming fails."""


@dataclass
class TrimChange:
    key: str
    original: str
    trimmed: str

    def as_dict(self) -> dict:
        return {
            "key": self.key,
            "original": self.original,
            "trimmed": self.trimmed,
        }


@dataclass
class TrimResult:
    source: str
    env: Dict[str, str]
    changes: List[TrimChange] = field(default_factory=list)

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


def trim_values(env: Dict[str, str], source: str = "") -> TrimResult:
    """Strip leading and trailing whitespace from all env values.

    Args:
        env: Mapping of key -> value (as returned by parse_env_file).
        source: Optional label for the origin of the env data.

    Returns:
        TrimResult with the cleaned env and a list of changed keys.

    Raises:
        TrimError: If *env* is not a dict.
    """
    if not isinstance(env, dict):
        raise TrimError("env must be a dict")

    trimmed_env: Dict[str, str] = {}
    changes: List[TrimChange] = []

    for key, value in env.items():
        clean = value.strip()
        trimmed_env[key] = clean
        if clean != value:
            changes.append(TrimChange(key=key, original=value, trimmed=clean))

    return TrimResult(source=source, env=trimmed_env, changes=changes)
