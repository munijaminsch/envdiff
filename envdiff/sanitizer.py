"""Sanitize .env file contents by redacting sensitive values."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


class SanitizeError(Exception):
    """Raised when sanitization fails."""


_DEFAULT_SENSITIVE_PATTERNS: List[str] = [
    r"(?i)password",
    r"(?i)secret",
    r"(?i)token",
    r"(?i)api[_]?key",
    r"(?i)private[_]?key",
    r"(?i)auth",
    r"(?i)credential",
]

REDACTED = "***REDACTED***"


@dataclass
class SanitizedEnv:
    """Result of sanitizing a parsed env mapping."""

    original: Dict[str, str]
    sanitized: Dict[str, str]
    redacted_keys: List[str] = field(default_factory=list)

    @property
    def redacted_count(self) -> int:
        return len(self.redacted_keys)

    def as_dict(self) -> dict:
        return {
            "sanitized": self.sanitized,
            "redacted_keys": self.redacted_keys,
            "redacted_count": self.redacted_count,
        }


def _compile_patterns(patterns: List[str]) -> List[re.Pattern]:
    try:
        return [re.compile(p) for p in patterns]
    except re.error as exc:
        raise SanitizeError(f"Invalid sensitive pattern: {exc}") from exc


def _is_sensitive(key: str, compiled: List[re.Pattern]) -> bool:
    return any(p.search(key) for p in compiled)


def sanitize(
    env: Dict[str, str],
    extra_patterns: Optional[List[str]] = None,
    redact_value: str = REDACTED,
) -> SanitizedEnv:
    """Return a SanitizedEnv with sensitive values replaced by *redact_value*."""
    if env is None:
        raise SanitizeError("env mapping must not be None")

    patterns = list(_DEFAULT_SENSITIVE_PATTERNS)
    if extra_patterns:
        patterns.extend(extra_patterns)

    compiled = _compile_patterns(patterns)
    sanitized: Dict[str, str] = {}
    redacted_keys: List[str] = []

    for key, value in env.items():
        if _is_sensitive(key, compiled):
            sanitized[key] = redact_value
            redacted_keys.append(key)
        else:
            sanitized[key] = value

    return SanitizedEnv(
        original=dict(env),
        sanitized=sanitized,
        redacted_keys=sorted(redacted_keys),
    )


def is_sensitive_key(
    key: str,
    extra_patterns: Optional[List[str]] = None,
) -> bool:
    """Return True if *key* matches any sensitive pattern.

    Useful for checking individual keys without sanitizing a full mapping.

    Args:
        key: The environment variable name to check.
        extra_patterns: Additional regex patterns to consider sensitive.
    """
    patterns = list(_DEFAULT_SENSITIVE_PATTERNS)
    if extra_patterns:
        patterns.extend(extra_patterns)
    compiled = _compile_patterns(patterns)
    return _is_sensitive(key, compiled)
