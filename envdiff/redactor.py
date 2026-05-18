"""Redact sensitive values in a parsed env dict, returning a sanitized copy with a change log."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

_DEFAULT_PATTERNS: List[str] = [
    r"password",
    r"passwd",
    r"secret",
    r"token",
    r"api[_-]?key",
    r"private[_-]?key",
    r"auth",
    r"credential",
]

REDACT_PLACEHOLDER = "***REDACTED***"


class RedactError(Exception):
    """Raised when redaction cannot be performed."""


@dataclass
class RedactedKey:
    key: str
    original_length: int

    def as_dict(self) -> dict:
        return {"key": self.key, "original_length": self.original_length}


@dataclass
class RedactResult:
    source: str
    redacted: Dict[str, str]
    redacted_keys: List[RedactedKey] = field(default_factory=list)

    @property
    def redact_count(self) -> int:
        return len(self.redacted_keys)

    @property
    def is_clean(self) -> bool:
        return self.redact_count == 0

    def as_dict(self) -> dict:
        return {
            "source": self.source,
            "redact_count": self.redact_count,
            "redacted_keys": [rk.as_dict() for rk in self.redacted_keys],
            "env": self.redacted,
        }


def _compile_patterns(patterns: List[str]) -> List[re.Pattern]:
    return [re.compile(p, re.IGNORECASE) for p in patterns]


def redact(
    env: Dict[str, str],
    source: str = "",
    patterns: Optional[List[str]] = None,
    placeholder: str = REDACT_PLACEHOLDER,
) -> RedactResult:
    """Return a RedactResult with sensitive values replaced by *placeholder*."""
    if env is None:
        raise RedactError("env must be a dict, got None")

    compiled = _compile_patterns(patterns if patterns is not None else _DEFAULT_PATTERNS)
    redacted_env: Dict[str, str] = {}
    redacted_keys: List[RedactedKey] = []

    for key, value in env.items():
        if any(pat.search(key) for pat in compiled):
            redacted_keys.append(RedactedKey(key=key, original_length=len(value)))
            redacted_env[key] = placeholder
        else:
            redacted_env[key] = value

    return RedactResult(source=source, redacted=redacted_env, redacted_keys=redacted_keys)
