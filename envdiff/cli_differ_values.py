"""CLI subcommand: envdiff values — compare values for shared keys."""
from __future__ import annotations

import argparse
import json
import sys

from envdiff.differ_values import ValueDiffError, diff_values
from envdiff.parser import EnvParseError, parse_env_file


def add_values_subparser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "values",
        help="Compare values for keys shared between two .env files.",
    )
    p.add_argument("left", help="Path to the left .env file.")
    p.add_argument("right", help="Path to the right .env file.")
    p.add_argument(
        "--keys",
        nargs="+",
        metavar="KEY",
        help="Restrict comparison to these keys only.",
    )
    p.add_argument(
        "--json",
        action="store_true",
        dest="output_json",
        help="Output results as JSON.",
    )
    p.add_argument(
        "--fail-on-diff",
        action="store_true",
        help="Exit with code 1 when any value differs.",
    )
    p.set_defaults(func=run_values)


def _print_text(result, file=sys.stdout) -> None:
    print(f"Left:  {result.left_source or '(unknown)'}", file=file)
    print(f"Right: {result.right_source or '(unknown)'}", file=file)
    print(f"Keys compared: {result.total_keys}", file=file)
    if result.is_clean:
        print("All values match.", file=file)
        return
    print(f"Changed: {result.changed_count}  Unchanged: {result.unchanged_count}", file=file)
    for entry in result.entries:
        if entry.changed:
            print(f"  ~ {entry.key}: {entry.left_value!r} -> {entry.right_value!r}", file=file)


def run_values(args: argparse.Namespace) -> int:
    try:
        left_env = parse_env_file(args.left)
        right_env = parse_env_file(args.right)
    except (EnvParseError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    try:
        result = diff_values(
            left_env,
            right_env,
            left_source=args.left,
            right_source=args.right,
            keys_only=args.keys if args.keys else None,
        )
    except ValueDiffError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if getattr(args, "output_json", False):
        print(json.dumps(result.as_dict(), indent=2))
    else:
        _print_text(result)

    if getattr(args, "fail_on_diff", False) and not result.is_clean:
        return 1
    return 0
