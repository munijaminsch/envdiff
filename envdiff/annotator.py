"""Annotate an env dict with metadata about each key."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


class AnnotateError(Exception):
    """Raised when annotation fails."""


@dataclass
class KeyAnnotation:
    key: str
    value: str
    is_empty: bool
    is_quoted: bool
    has_whitespace_value: bool
    char_count: int
    tags: List[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "key": self.key,
            "value": self.value,
            "is_empty": self.is_empty,
            "is_quoted": self.is_quoted,
            "has_whitespace_value": self.has_whitespace_value,
            "char_count": self.char_count,
            "tags": self.tags,
        }


@dataclass
class AnnotationResult:
    source: str
    annotations: Dict[str, KeyAnnotation] = field(default_factory=dict)

    @property
    def total_keys(self) -> int:
        return len(self.annotations)

    @property
    def empty_keys(self) -> List[str]:
        return [k for k, a in self.annotations.items() if a.is_empty]

    @property
    def whitespace_keys(self) -> List[str]:
        return [k for k, a in self.annotations.items() if a.has_whitespace_value]

    def as_dict(self) -> dict:
        return {
            "source": self.source,
            "total_keys": self.total_keys,
            "annotations": {k: v.as_dict() for k, v in self.annotations.items()},
        }


def _detect_tags(key: str, value: str) -> List[str]:
    tags: List[str] = []
    lower = key.lower()
    if any(word in lower for word in ("secret", "password", "token", "key", "api")):
        tags.append("sensitive")
    if value.startswith("http://") or value.startswith("https://"):
        tags.append("url")
    if value.isdigit():
        tags.append("numeric")
    if value.lower() in ("true", "false"):
        tags.append("boolean")
    return tags


def annotate(env: Dict[str, str], source: str = "") -> AnnotationResult:
    """Produce an AnnotationResult for the given env mapping."""
    if not isinstance(env, dict):
        raise AnnotateError("env must be a dict")

    result = AnnotationResult(source=source)
    for key, value in env.items():
        stripped = value.strip()
        annotation = KeyAnnotation(
            key=key,
            value=value,
            is_empty=value == "",
            is_quoted=(
                (value.startswith('"') and value.endswith('"'))
                or (value.startswith("'") and value.endswith("'"))
            ),
            has_whitespace_value=stripped != value and value != "",
            char_count=len(value),
            tags=_detect_tags(key, stripped),
        )
        result.annotations[key] = annotation
    return result
