"""CLI subcommand: lint — check .env files for common issues."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.linter import lint_file, LintError


def add_lint_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    parser = subparsers.add_parser("lint", help="Lint .env files for common issues")
    parser.add_argument("files", nargs="+", metavar="FILE", help=".env files to lint")
    parser.add_argument(
        "--strict",
        action="store_true",
        default=False,
        help="Exit with code 1 if any warnings are found",
    )


def run_lint(args: argparse.Namespace, out=sys.stdout, err=sys.stderr) -> int:
    """Run lint subcommand. Returns exit code."""
    any_issues = False

    for file_path in args.files:
        try:
            result = lint_file(file_path)
        except LintError as exc:
            print(f"ERROR: {exc}", file=err)
            return 2

        if result.is_clean:
            print(f"{file_path}: OK", file=out)
        else:
            any_issues = True
            print(f"{file_path}:", file=out)
            for issue in result.issues:
                print(f"  {issue}", file=out)

    if any_issues and args.strict:
        return 1
    return 0
