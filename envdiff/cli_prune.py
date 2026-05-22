"""CLI sub-command: prune — remove keys not in an allow-list."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List

from envdiff.parser import parse_env_file, EnvParseError
from envdiff.pruner import prune, PruneError


def add_prune_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser("prune", help="Remove keys not in an allow-list from an env file.")
    p.add_argument("file", help="Path to the .env file to prune.")
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--keys",
        nargs="+",
        metavar="KEY",
        help="Explicit keys to keep.",
    )
    group.add_argument(
        "--patterns",
        nargs="+",
        metavar="PATTERN",
        help="Regex patterns; matching keys are kept.",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="fmt",
        help="Output format (default: text).",
    )
    p.add_argument(
        "--strict",
        action="store_true",
        help="Exit with code 1 if any keys were removed.",
    )


def run_prune(args: argparse.Namespace) -> int:
    try:
        env = parse_env_file(args.file)
    except EnvParseError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    try:
        result = prune(
            env,
            allowed_keys=args.keys,
            allowed_patterns=args.patterns,
            source=args.file,
        )
    except PruneError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.fmt == "json":
        print(json.dumps(result.as_dict(), indent=2))
    else:
        _print_text(result)

    if args.strict and not result.is_clean:
        return 1
    return 0


def _print_text(result) -> None:
    print(f"Source : {result.source}")
    print(f"Kept   : {result.kept_count}")
    print(f"Removed: {result.removed_count}")
    if result.removed_count:
        print("Removed keys:")
        for entry in result.entries:
            if entry.removed:
                print(f"  - {entry.key}")
