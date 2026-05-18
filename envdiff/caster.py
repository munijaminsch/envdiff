"""Type-casting module: infers and casts .env values to Python native types."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class CastError(Exception):
    """Raised when casting fails unexpectedly."""


_TRUE_VALUES = {"true", "yes", "1", "on"}
_FALSE_VALUES = {"false", "no", "0", "off"}


def _cast_value(raw: str) -> Any:
    """Attempt to cast a raw string to bool, int, float, or leave as str."""
    stripped = raw.strip()
    if stripped.lower() in _TRUE_VALUES:
        return True
    if stripped.lower() in _FALSE_VALUES:
        return False
    try:
        return int(stripped)
    except ValueError:
        pass
    try:
        return float(stripped)
    except ValueError:
        pass
    return stripped


@dataclass
class CastEntry:
    key: str
    raw: str
    cast_value: Any
    cast_type: str

    def as_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "raw": self.raw,
            "cast_value": self.cast_value,
            "cast_type": self.cast_type,
        }


@dataclass
class CastResult:
    source: str
    entries: List[CastEntry] = field(default_factory=list)

    @property
    def total_keys(self) -> int:
        return len(self.entries)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "total_keys": self.total_keys,
            "entries": [e.as_dict() for e in self.entries],
        }


def cast_env(env: Dict[str, str], source: str = "") -> CastResult:
    """Cast all values in an env dict and return a CastResult."""
    if env is None:
        raise CastError("env must not be None")
    entries: List[CastEntry] = []
    for key, raw in env.items():
        value = _cast_value(raw)
        entries.append(
            CastEntry(
                key=key,
                raw=raw,
                cast_value=value,
                cast_type=type(value).__name__,
            )
        )
    return CastResult(source=source, entries=entries)
