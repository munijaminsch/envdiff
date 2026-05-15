"""Validates that .env values conform to expected types or patterns."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


class ValidateError(Exception):
    """Raised when validation setup is invalid."""


@dataclass
class ValidationIssue:
    key: str
    value: str
    rule: str
    message: str

    def __str__(self) -> str:
        return f"{self.key}={self.value!r}: {self.message} (rule: {self.rule})"


@dataclass
class ValidationResult:
    file: str
    issues: List[ValidationIssue] = field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        return len(self.issues) == 0

    def as_dict(self) -> dict:
        return {
            "file": self.file,
            "is_clean": self.is_clean,
            "issues": [
                {"key": i.key, "value": i.value, "rule": i.rule, "message": i.message}
                for i in self.issues
            ],
        }


# Built-in rule names and their patterns
_BUILTIN_RULES: Dict[str, re.Pattern] = {
    "nonempty": re.compile(r".+"),
    "alphanumeric": re.compile(r"^[A-Za-z0-9]+$"),
    "numeric": re.compile(r"^-?\d+(\.\d+)?$"),
    "url": re.compile(r"^https?://\S+$"),
    "boolean": re.compile(r"^(true|false|1|0|yes|no)$", re.IGNORECASE),
}


def _get_pattern(rule: str) -> re.Pattern:
    if rule in _BUILTIN_RULES:
        return _BUILTIN_RULES[rule]
    try:
        return re.compile(rule)
    except re.error as exc:
        raise ValidateError(f"Invalid rule pattern {rule!r}: {exc}") from exc


def validate_env(
    env: Dict[str, str],
    rules: Dict[str, str],
    file: str = "<unknown>",
    required_keys: Optional[List[str]] = None,
) -> ValidationResult:
    """Validate *env* dict against *rules* mapping key -> rule name or regex.

    Args:
        env: Parsed key/value pairs.
        rules: Mapping of env key to a built-in rule name or regex string.
        file: Label used in the result (e.g. file path).
        required_keys: Keys that must be present regardless of rules.

    Returns:
        ValidationResult with any issues found.
    """
    result = ValidationResult(file=file)

    for key in required_keys or []:
        if key not in env:
            result.issues.append(
                ValidationIssue(
                    key=key,
                    value="",
                    rule="required",
                    message=f"Key '{key}' is required but missing",
                )
            )

    for key, rule in rules.items():
        if key not in env:
            continue
        value = env[key]
        pattern = _get_pattern(rule)
        if not pattern.search(value):
            result.issues.append(
                ValidationIssue(
                    key=key,
                    value=value,
                    rule=rule,
                    message=f"Value does not match rule '{rule}'",
                )
            )

    return result
