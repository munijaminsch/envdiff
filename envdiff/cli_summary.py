"""CLI sub-command: summarise a diff between two .env files."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List

from envdiff.parser import parse_env_file, EnvParseError
from envdiff.comparator import compare
from envdiff.differ_summary import build_diff_summary, SummaryError


def add_summary_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    parser = subparsers.add_parser(
        "summary",
        help="Print a structured summary of differences between two .env files.",
    )
    parser.add_argument("left", help="Path to the left .env file")
    parser.add_argument("right", help="Path to the right .env file")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="fmt",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--fail-on-diff",
        action="store_true",
        default=False,
        help="Exit with code 1 when differences are found",
    )
    parser.set_defaults(func=run_summary)


def run_summary(args: argparse.Namespace) -> int:
    """Execute the summary sub-command. Returns exit code."""
    try:
        left_env = parse_env_file(args.left)
        right_env = parse_env_file(args.right)
    except EnvParseError as exc:
        print(f"Parse error: {exc}", file=sys.stderr)
        return 2

    try:
        result = compare(left_env, right_env, args.left, args.right)
        summary = build_diff_summary(result)
    except SummaryError as exc:
        print(f"Summary error: {exc}", file=sys.stderr)
        return 2

    if args.fmt == "json":
        print(json.dumps(summary.as_dict(), indent=2))
    else:
        _print_text(summary)

    if args.fail_on_diff and not summary.is_clean:
        return 1
    return 0


def _print_text(summary) -> None:
    print(f"Comparing: {summary.left_file}  vs  {summary.right_file}")
    print(f"Keys: {summary.total_keys}  Issues: {summary.issue_count}")
    print()
    for line in summary.lines:
        marker = "✓" if line.status == "match" else "✗"
        print(f"  {marker} [{line.status:<14}] {line.key}")
        if line.status != "match":
            print(f"      {line.detail}")
    print()
    if summary.is_clean:
        print("No differences found.")
    else:
        print(f"{summary.issue_count} issue(s) found.")
