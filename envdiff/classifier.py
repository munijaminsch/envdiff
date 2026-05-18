"""Classify env keys by inferred type based on their values."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


class ClassifyError(Exception):
    """Raised when classification fails."""


_BOOL_VALUES = {"true", "false", "yes", "no", "1", "0", "on", "off"}
_URL_RE = re.compile(r"^https?://", re.IGNORECASE)
_INT_RE = re.compile(r"^-?\d+$")
_FLOAT_RE = re.compile(r"^-?\d+\.\d+$")
_PATH_RE = re.compile(r"^[/~.][\\/]")


def _infer_type(value: str) -> str:
    if value == "":
        return "empty"
    if value.lower() in _BOOL_VALUES:
        return "boolean"
    if _INT_RE.match(value):
        return "integer"
    if _FLOAT_RE.match(value):
        return "float"
    if _URL_RE.match(value):
        return "url"
    if _PATH_RE.match(value):
        return "path"
    return "string"


@dataclass
class KeyClassification:
    key: str
    value: str
    inferred_type: str

    def as_dict(self) -> dict:
        return {"key": self.key, "value": self.value, "type": self.inferred_type}


@dataclass
class ClassifyResult:
    source: str
    classifications: List[KeyClassification] = field(default_factory=list)

    @property
    def total_keys(self) -> int:
        return len(self.classifications)

    def by_type(self) -> Dict[str, List[KeyClassification]]:
        result: Dict[str, List[KeyClassification]] = {}
        for c in self.classifications:
            result.setdefault(c.inferred_type, []).append(c)
        return result

    def as_dict(self) -> dict:
        return {
            "source": self.source,
            "total_keys": self.total_keys,
            "classifications": [c.as_dict() for c in self.classifications],
        }


def classify_env(env: Dict[str, str], source: str = "") -> ClassifyResult:
    """Classify each key in *env* by its inferred value type."""
    if env is None:
        raise ClassifyError("env must not be None")
    classifications = [
        KeyClassification(key=k, value=v, inferred_type=_infer_type(v))
        for k, v in sorted(env.items())
    ]
    return ClassifyResult(source=source, classifications=classifications)
