"""CLI sub-command: count  — compare key counts between two .env files."""
from __future__ import annotations

import json
import sys

from envdiff.differ_count import CountDiffError, diff_counts
from envdiff.parser import EnvParseError, parse_env_file


def add_count_subparser(subparsers) -> None:
    p = subparsers.add_parser(
        "count",
        help="Compare the number of keys between two .env files.",
    )
    p.add_argument("left", help="Path to the left .env file.")
    p.add_argument("right", help="Path to the right .env file.")
    p.add_argument(
        "--json",
        dest="as_json",
        action="store_true",
        default=False,
        help="Output result as JSON.",
    )
    p.add_argument(
        "--strict",
        action="store_true",
        default=False,
        help="Exit with code 1 when counts differ.",
    )
    p.set_defaults(func=run_count)


def _print_text(result) -> None:
    print(f"Left  ({result.left_source}): {result.left_total} key(s)")
    print(f"Right ({result.right_source}): {result.right_total} key(s)")
    print(f"Delta: {result.net_delta:+d}")
    if not result.is_clean:
        print("\nKey breakdown:")
        for entry in result.entries:
            if entry.delta != 0:
                direction = "only in left" if entry.delta < 0 else "only in right"
                print(f"  {entry.key}: {direction}")


def run_count(args) -> int:
    try:
        left_env = parse_env_file(args.left)
        right_env = parse_env_file(args.right)
    except EnvParseError as exc:
        print(f"Parse error: {exc}", file=sys.stderr)
        return 2

    try:
        result = diff_counts(
            left_env,
            right_env,
            left_source=args.left,
            right_source=args.right,
        )
    except CountDiffError as exc:
        print(f"Count diff error: {exc}", file=sys.stderr)
        return 2

    if args.as_json:
        print(json.dumps(result.as_dict(), indent=2))
    else:
        _print_text(result)

    if args.strict and not result.is_clean:
        return 1
    return 0
