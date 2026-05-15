"""Command-line interface for envdiff."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.comparator import compare
from envdiff.formatter import get_formatter
from envdiff.parser import EnvParseError, parse_env_file


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envdiff",
        description="Compare .env files across environments.",
    )
    parser.add_argument("left", type=Path, help="First .env file (e.g. .env.staging)")
    parser.add_argument("right", type=Path, help="Second .env file (e.g. .env.production)")
    parser.add_argument(
        "--format",
        dest="fmt",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--exit-code",
        action="store_true",
        default=False,
        help="Exit with code 1 when differences are found",
    )
    return parser


def run(argv: list[str] | None = None) -> int:
    """Entry point; returns an exit code."""
    args = build_parser().parse_args(argv)

    for path in (args.left, args.right):
        if not path.exists():
            print(f"envdiff: error: file not found: {path}", file=sys.stderr)
            return 2

    try:
        left_env = parse_env_file(args.left)
        right_env = parse_env_file(args.right)
    except EnvParseError as exc:
        print(f"envdiff: parse error: {exc}", file=sys.stderr)
        return 2

    result = compare(left_env, right_env)
    formatter = get_formatter(args.fmt)
    env_names = (args.left.name, args.right.name)
    print(formatter.format(result, env_names))

    if args.exit_code and result.has_differences():
        return 1
    return 0


def main() -> None:  # pragma: no cover
    sys.exit(run())


if __name__ == "__main__":  # pragma: no cover
    main()
