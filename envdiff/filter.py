"""Filter utilities for narrowing comparison results by key patterns."""

from __future__ import annotations

import fnmatch
import re
from typing import Iterable

from envdiff.comparator import CompareResult, KeyDiff


class FilterError(Exception):
    """Raised when a filter pattern is invalid."""


def _compile_pattern(pattern: str) -> re.Pattern:
    """Compile a glob-style pattern into a regex, raising FilterError on failure."""
    try:
        return re.compile(fnmatch.translate(pattern), re.IGNORECASE)
    except re.error as exc:
        raise FilterError(f"Invalid pattern {pattern!r}: {exc}") from exc


def filter_keys(
    result: CompareResult,
    include: Iterable[str] | None = None,
    exclude: Iterable[str] | None = None,
) -> CompareResult:
    """Return a new CompareResult containing only diffs whose keys match the
    given include/exclude glob patterns.

    Args:
        result:  The original CompareResult to filter.
        include: If provided, only keys matching at least one pattern are kept.
        exclude: If provided, keys matching any pattern are removed.

    Returns:
        A new CompareResult with filtered diffs.
    """
    include_patterns = [_compile_pattern(p) for p in (include or [])]
    exclude_patterns = [_compile_pattern(p) for p in (exclude or [])]

    def _keep(diff: KeyDiff) -> bool:
        key = diff.key
        if exclude_patterns and any(p.match(key) for p in exclude_patterns):
            return False
        if include_patterns and not any(p.match(key) for p in include_patterns):
            return False
        return True

    filtered_diffs = [d for d in result.diffs if _keep(d)]
    return CompareResult(
        left_file=result.left_file,
        right_file=result.right_file,
        diffs=filtered_diffs,
    )


def filter_by_prefix(result: CompareResult, prefix: str) -> CompareResult:
    """Convenience wrapper that keeps only keys starting with *prefix* (case-insensitive)."""
    return filter_keys(result, include=[f"{prefix}*"])
