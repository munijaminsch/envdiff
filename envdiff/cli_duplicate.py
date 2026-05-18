"""CLI sub-command: envdiff duplicates — find duplicate values in an env file."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List

from envdiff.parser import parse_env_file, EnvParseError
from envdiff.duplicator import find_duplicates, DuplicateError


def add_duplicate_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "duplicates",
        help="Find keys that share identical values within an env file.",
    )
    p.add_argument("file", help="Path to the .env file to inspect.")
    p.add_argument(
        "--ignore-empty",
        action="store_true",
        default=False,
        help="Skip keys whose value is an empty string.",
    )
    p.add_argument(
        "--json",
        dest="output_json",
        action="store_true",
        default=False,
        help="Output results as JSON.",
    )
    p.add_argument(
        "--exit-code",
        action="store_true",
        default=False,
        help="Exit with code 1 when duplicates are found.",
    )
    p.set_defaults(func=run_duplicate)


def run_duplicate(args: argparse.Namespace) -> int:
    """Execute the duplicates sub-command; return an exit code."""
    try:
        env = parse_env_file(args.file)
    except (EnvParseError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    try:
        result = find_duplicates(
            env,
            source=args.file,
            ignore_empty=args.ignore_empty,
        )
    except DuplicateError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if getattr(args, "output_json", False):
        print(json.dumps(result.as_dict(), indent=2))
    else:
        _print_text(result.source, result.groups)

    if args.exit_code and not result.is_clean:
        return 1
    return 0


def _print_text(source: str, groups) -> None:
    if not groups:
        print(f"No duplicate values found in {source}")
        return

    print(f"Duplicate values in {source}:")
    for group in groups:
        keys_str = ", ".join(sorted(group.keys))
        print(f"  value={group.value!r}  keys=[{keys_str}]")
