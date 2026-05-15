"""Lint .env files for common issues like duplicate keys, empty values, and invalid formats."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from envdiff.parser import parse_env_file, EnvParseError


class LintError(Exception):
    """Raised when linting cannot proceed."""


@dataclass
class LintIssue:
    line: int
    code: str
    message: str

    def __str__(self) -> str:
        return f"Line {self.line} [{self.code}]: {self.message}"


@dataclass
class LintResult:
    path: str
    issues: List[LintIssue] = field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        return len(self.issues) == 0

    def add(self, issue: LintIssue) -> None:
        self.issues.append(issue)


def lint_file(path: str | Path) -> LintResult:
    """Lint a single .env file and return a LintResult with any issues found."""
    path = Path(path)
    result = LintResult(path=str(path))

    try:
        raw_lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise LintError(f"Cannot read file: {path}") from exc

    seen_keys: dict[str, int] = {}

    for lineno, raw in enumerate(raw_lines, start=1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if "=" not in stripped:
            result.add(LintIssue(lineno, "E001", f"Invalid format (missing '='): {stripped!r}"))
            continue

        key, _, value = stripped.partition("=")
        key = key.strip()
        value = value.strip()

        if not key:
            result.add(LintIssue(lineno, "E002", "Empty key name"))
            continue

        if key in seen_keys:
            result.add(LintIssue(lineno, "W001", f"Duplicate key '{key}' (first seen on line {seen_keys[key]})"))
        else:
            seen_keys[key] = lineno

        if value == "" or value in ("\"\"", "''"):
            result.add(LintIssue(lineno, "W002", f"Empty value for key '{key}'"))

    return result
