"""High-level diff orchestration: parse, compare, and optionally filter."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Sequence

from envdiff.comparator import CompareResult, compare
from envdiff.filter import FilterError, filter_by_prefix, filter_keys
from envdiff.parser import EnvParseError, parse_env_file


class DiffError(Exception):
    """Raised when the diff pipeline encounters an unrecoverable error."""


@dataclass
class DiffOptions:
    include_patterns: Sequence[str] = field(default_factory=list)
    exclude_patterns: Sequence[str] = field(default_factory=list)
    prefix: Optional[str] = None


def diff_files(
    left_path: Path,
    right_path: Path,
    options: Optional[DiffOptions] = None,
) -> CompareResult:
    """Parse two .env files, apply optional filters, and return a CompareResult.

    Args:
        left_path: Path to the first .env file.
        right_path: Path to the second .env file.
        options: Optional filtering options to apply before comparison.

    Returns:
        A CompareResult describing the differences.

    Raises:
        DiffError: If parsing or filtering fails.
    """
    try:
        left = parse_env_file(left_path)
        right = parse_env_file(right_path)
    except EnvParseError as exc:
        raise DiffError(f"Failed to parse env file: {exc}") from exc

    if options is None:
        options = DiffOptions()

    try:
        if options.prefix:
            left = filter_by_prefix(left, options.prefix)
            right = filter_by_prefix(right, options.prefix)

        if options.include_patterns:
            left = filter_keys(left, include=list(options.include_patterns))
            right = filter_keys(right, include=list(options.include_patterns))

        if options.exclude_patterns:
            left = filter_keys(left, exclude=list(options.exclude_patterns))
            right = filter_keys(right, exclude=list(options.exclude_patterns))
    except FilterError as exc:
        raise DiffError(f"Failed to apply filter: {exc}") from exc

    return compare(left, right, left_name=left_path.name, right_name=right_path.name)
