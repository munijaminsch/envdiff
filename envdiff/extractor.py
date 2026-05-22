"""Extract a subset of keys from an env mapping into a new dict."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional


class ExtractError(Exception):
    """Raised when extraction cannot be completed."""


@dataclass
class ExtractedKey:
    key: str
    value: str

    def as_dict(self) -> dict:
        return {"key": self.key, "value": self.value}


@dataclass
class ExtractResult:
    source: str
    keys_requested: List[str]
    entries: List[ExtractedKey] = field(default_factory=list)
    missing: List[str] = field(default_factory=list)

    @property
    def total_keys(self) -> int:
        return len(self.entries)

    @property
    def is_complete(self) -> bool:
        """True when every requested key was found."""
        return len(self.missing) == 0

    def as_dict(self) -> dict:
        return {
            "source": self.source,
            "keys_requested": self.keys_requested,
            "total_keys": self.total_keys,
            "is_complete": self.is_complete,
            "entries": [e.as_dict() for e in self.entries],
            "missing": self.missing,
        }


def extract_keys(
    env: Dict[str, str],
    keys: Iterable[str],
    *,
    source: Optional[str] = None,
) -> ExtractResult:
    """Return an :class:`ExtractResult` containing only the requested *keys*.

    Keys that are absent from *env* are recorded in
    :attr:`ExtractResult.missing` rather than raising an error.
    """
    if env is None:
        raise ExtractError("env mapping must not be None")

    key_list = list(keys)
    if not key_list:
        raise ExtractError("at least one key must be requested")

    entries: List[ExtractedKey] = []
    missing: List[str] = []

    for key in key_list:
        if key in env:
            entries.append(ExtractedKey(key=key, value=env[key]))
        else:
            missing.append(key)

    return ExtractResult(
        source=source or "",
        keys_requested=key_list,
        entries=entries,
        missing=missing,
    )
