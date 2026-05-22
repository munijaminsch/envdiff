"""cli_linker.py — CLI subcommand: link two .env files and display cross-reference."""
from __future__ import annotations

import json
import sys
from argparse import ArgumentParser, Namespace
from typing import List

from envdiff.parser import parse_env_file, EnvParseError
from envdiff.linker import link_envs, LinkError


def add_link_subparser(subparsers) -> None:
    p: ArgumentParser = subparsers.add_parser(
        "link",
        help="Cross-reference keys between two .env files.",
    )
    p.add_argument("left", help="Path to the left .env file.")
    p.add_argument("right", help="Path to the right .env file.")
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="fmt",
        help="Output format (default: text).",
    )
    p.add_argument(
        "--fail-on-diff",
        action="store_true",
        default=False,
        help="Exit with code 1 when shared keys have mismatched values.",
    )
    p.set_defaults(func=run_link)


def _print_text(result, file=sys.stdout) -> None:
    print(f"Left:  {result.left_source}", file=file)
    print(f"Right: {result.right_source}", file=file)
    print(f"Total keys: {result.total_keys}", file=file)
    print(f"Shared: {len(result.shared_keys)}  "
          f"Left-only: {len(result.exclusive_left)}  "
          f"Right-only: {len(result.exclusive_right)}", file=file)
    if result.exclusive_left:
        print("\nOnly in left:", file=file)
        for k in result.exclusive_left:
            print(f"  - {k}", file=file)
    if result.exclusive_right:
        print("\nOnly in right:", file=file)
        for k in result.exclusive_right:
            print(f"  - {k}", file=file)
    mismatched = [e for e in result.entries if e.is_shared and not e.values_match]
    if mismatched:
        print("\nValue mismatches:", file=file)
        for e in mismatched:
            print(f"  {e.key}: {e.left_value!r} != {e.right_value!r}", file=file)
    if result.is_clean:
        print("\nAll shared keys match.", file=file)


def run_link(args: Namespace) -> int:
    try:
        left = parse_env_file(args.left)
        right = parse_env_file(args.right)
    except EnvParseError as exc:
        print(f"Parse error: {exc}", file=sys.stderr)
        return 2

    try:
        result = link_envs(left, right, left_source=args.left, right_source=args.right)
    except LinkError as exc:
        print(f"Link error: {exc}", file=sys.stderr)
        return 2

    if args.fmt == "json":
        print(json.dumps(result.as_dict(), indent=2))
    else:
        _print_text(result)

    if args.fail_on_diff and not result.is_clean:
        return 1
    return 0
