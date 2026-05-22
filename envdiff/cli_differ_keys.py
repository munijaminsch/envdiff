"""CLI subcommand: keys — show keys exclusive to one side of a diff."""
from __future__ import annotations

import json
import sys
from argparse import ArgumentParser, Namespace

from envdiff.differ_keys import KeyDiffError, diff_keys
from envdiff.parser import EnvParseError, parse_env_file


def add_keys_subparser(subparsers) -> None:
    p: ArgumentParser = subparsers.add_parser(
        "keys",
        help="Show keys that exist in only one of two .env files.",
    )
    p.add_argument("left", help="First .env file")
    p.add_argument("right", help="Second .env file")
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="fmt",
        help="Output format (default: text)",
    )
    p.add_argument(
        "--fail",
        action="store_true",
        help="Exit with code 1 if any exclusive keys are found.",
    )
    p.set_defaults(func=run_keys)


def run_keys(args: Namespace) -> int:
    try:
        left_env = parse_env_file(args.left)
        right_env = parse_env_file(args.right)
    except EnvParseError as exc:
        print(f"Parse error: {exc}", file=sys.stderr)
        return 1

    try:
        result = diff_keys(
            left_env,
            right_env,
            left_source=args.left,
            right_source=args.right,
        )
    except KeyDiffError as exc:
        print(f"Diff error: {exc}", file=sys.stderr)
        return 1

    if args.fmt == "json":
        print(json.dumps(result.as_dict(), indent=2))
    else:
        _print_text(result)

    if args.fail and not result.is_clean:
        return 1
    return 0


def _print_text(result) -> None:
    if result.is_clean:
        print("No exclusive keys found.")
        return
    if result.only_in_left:
        print(f"Only in {result.left_source or 'left'}:")
        for entry in result.only_in_left:
            print(f"  {entry.key}={entry.value}")
    if result.only_in_right:
        print(f"Only in {result.right_source or 'right'}:")
        for entry in result.only_in_right:
            print(f"  {entry.key}={entry.value}")
