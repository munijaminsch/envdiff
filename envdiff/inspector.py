"""Inspect a parsed env dict and produce a structured report of key metadata."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


class InspectError(Exception):
    """Raised when inspection fails."""


@dataclass
class KeyInspection:
    key: str
    value: str
    length: int
    is_empty: bool
    is_numeric: bool
    is_boolean: bool
    has_whitespace: bool
    uppercase: bool

    def as_dict(self) -> dict:
        return {
            "key": self.key,
            "value": self.value,
            "length": self.length,
            "is_empty": self.is_empty,
            "is_numeric": self.is_numeric,
            "is_boolean": self.is_boolean,
            "has_whitespace": self.has_whitespace,
            "uppercase": self.uppercase,
        }


@dataclass
class InspectResult:
    source: str
    inspections: List[KeyInspection] = field(default_factory=list)

    @property
    def total_keys(self) -> int:
        return len(self.inspections)

    @property
    def empty_keys(self) -> List[str]:
        return [i.key for i in self.inspections if i.is_empty]

    @property
    def numeric_keys(self) -> List[str]:
        return [i.key for i in self.inspections if i.is_numeric]

    @property
    def boolean_keys(self) -> List[str]:
        return [i.key for i in self.inspections if i.is_boolean]

    def as_dict(self) -> dict:
        return {
            "source": self.source,
            "total_keys": self.total_keys,
            "empty_keys": self.empty_keys,
            "numeric_keys": self.numeric_keys,
            "boolean_keys": self.boolean_keys,
            "inspections": [i.as_dict() for i in self.inspections],
        }


_BOOLEAN_VALUES = {"true", "false", "yes", "no", "1", "0", "on", "off"}


def inspect_env(env: Dict[str, str], source: str = "") -> InspectResult:
    """Inspect each key in *env* and return an InspectResult."""
    if env is None:
        raise InspectError("env must not be None")

    inspections: List[KeyInspection] = []
    for key, value in env.items():
        inspections.append(
            KeyInspection(
                key=key,
                value=value,
                length=len(value),
                is_empty=value == "",
                is_numeric=_is_numeric(value),
                is_boolean=value.lower() in _BOOLEAN_VALUES,
                has_whitespace=any(c in value for c in (" ", "\t")),
                uppercase=key == key.upper(),
            )
        )
    return InspectResult(source=source, inspections=inspections)


def _is_numeric(value: str) -> bool:
    if value == "":
        return False
    try:
        float(value)
        return True
    except ValueError:
        return False
