"""CLI sub-command: multi — diff more than two .env files at once."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List

from envdiff.differ_multi import MultiDiffError, diff_multi


def add_multi_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "multi",
        help="Compare more than two .env files simultaneously.",
    )
    p.add_argument("files", nargs="+", metavar="FILE", help=".env files to compare")
    p.add_argument(
        "--json", dest="as_json", action="store_true", help="Output as JSON"
    )
    p.add_argument(
        "--fail-on-diff",
        action="store_true",
        help="Exit with code 1 when any differences are found",
    )


def run_multi(args: argparse.Namespace) -> int:
    try:
        result = diff_multi(args.files)
    except MultiDiffError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.as_json:
        print(json.dumps(result.as_dict(), indent=2))
    else:
        _print_text(result)

    if args.fail_on_diff and not result.is_clean():
        return 1
    return 0


def _print_text(result) -> None:  # type: ignore[no-untyped-def]
    if result.is_clean():
        print("All files match — no differences found.")
        return

    for pair in result.pairs:
        if not pair.result.has_differences():
            continue
        print(f"\n--- {pair.left}")
        print(f"+++ {pair.right}")
        for k in pair.result.missing_in_right():
            print(f"  MISSING IN RIGHT : {k}")
        for k in pair.result.missing_in_left():
            print(f"  MISSING IN LEFT  : {k}")
        for diff in pair.result.mismatched_keys():
            print(f"  MISMATCH         : {diff.key}")
