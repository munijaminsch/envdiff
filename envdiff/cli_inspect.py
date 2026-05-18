"""CLI sub-command: inspect — display key metadata for a .env file."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from envdiff.inspector import InspectError, inspect_env
from envdiff.parser import EnvParseError, parse_env_file


def add_inspect_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    parser = subparsers.add_parser(
        "inspect",
        help="Inspect key metadata in a .env file.",
    )
    parser.add_argument("file", help="Path to the .env file to inspect.")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="fmt",
        help="Output format (default: text).",
    )
    parser.add_argument(
        "--only-issues",
        action="store_true",
        help="Only show keys with notable characteristics (empty, whitespace).",
    )
    parser.set_defaults(func=run_inspect)


def run_inspect(args: argparse.Namespace) -> int:
    path = Path(args.file)
    try:
        env = parse_env_file(path)
    except (EnvParseError, FileNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    try:
        result = inspect_env(env, source=str(path))
    except InspectError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.fmt == "json":
        print(json.dumps(result.as_dict(), indent=2))
        return 0

    _print_text(result, only_issues=getattr(args, "only_issues", False))
    return 0


def _print_text(result, *, only_issues: bool = False) -> None:
    print(f"File   : {result.source}")
    print(f"Keys   : {result.total_keys}")
    if result.empty_keys:
        print(f"Empty  : {', '.join(result.empty_keys)}")
    if result.numeric_keys:
        print(f"Numeric: {', '.join(result.numeric_keys)}")
    if result.boolean_keys:
        print(f"Boolean: {', '.join(result.boolean_keys)}")
    print()
    for insp in result.inspections:
        if only_issues and not (insp.is_empty or insp.has_whitespace):
            continue
        flags = []
        if insp.is_empty:
            flags.append("empty")
        if insp.has_whitespace:
            flags.append("whitespace")
        if insp.is_numeric:
            flags.append("numeric")
        if insp.is_boolean:
            flags.append("boolean")
        tag = f"  [{', '.join(flags)}]" if flags else ""
        print(f"  {insp.key}={insp.value!r}{tag}")
