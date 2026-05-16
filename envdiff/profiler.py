"""Profiles .env files and produces a statistical summary of their contents."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

from envdiff.parser import parse_env_file


class ProfileError(Exception):
    """Raised when profiling fails."""


@dataclass
class EnvProfile:
    """Statistical profile of a single .env file."""

    path: str
    total_keys: int
    empty_values: List[str] = field(default_factory=list)
    duplicate_values: Dict[str, List[str]] = field(default_factory=dict)
    longest_key: str = ""
    longest_value_key: str = ""

    @property
    def empty_count(self) -> int:
        return len(self.empty_values)

    @property
    def duplicate_value_groups(self) -> int:
        return len(self.duplicate_values)

    def as_dict(self) -> dict:
        return {
            "path": self.path,
            "total_keys": self.total_keys,
            "empty_count": self.empty_count,
            "empty_values": self.empty_values,
            "duplicate_value_groups": self.duplicate_value_groups,
            "duplicate_values": self.duplicate_values,
            "longest_key": self.longest_key,
            "longest_value_key": self.longest_value_key,
        }


def profile_env_file(path: str | Path) -> EnvProfile:
    """Parse and profile a single .env file."""
    resolved = Path(path)
    if not resolved.exists():
        raise ProfileError(f"File not found: {path}")

    try:
        env = parse_env_file(resolved)
    except Exception as exc:
        raise ProfileError(f"Failed to parse {path}: {exc}") from exc

    empty_values = [k for k, v in env.items() if v == ""]

    # Group keys that share the same non-empty value
    value_map: Dict[str, List[str]] = {}
    for k, v in env.items():
        if v:
            value_map.setdefault(v, []).append(k)
    duplicate_values = {v: keys for v, keys in value_map.items() if len(keys) > 1}

    longest_key = max(env.keys(), key=len, default="")
    longest_value_key = max(env.keys(), key=lambda k: len(env[k]), default="")

    return EnvProfile(
        path=str(resolved),
        total_keys=len(env),
        empty_values=empty_values,
        duplicate_values=duplicate_values,
        longest_key=longest_key,
        longest_value_key=longest_value_key,
    )
