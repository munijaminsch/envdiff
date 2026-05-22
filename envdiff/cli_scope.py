"""CLI sub-command: scope — filter env keys by environment scope prefix."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List

from envdiff.parser import parse_env_file, EnvParseError
from envdiff.scoper import scope_env, ScopeError


def add_scope_subparser(subparsers) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "scope",
        help="Filter keys belonging to a named scope prefix (e.g. PROD__)",
    )
    p.add_argument("file", help="Path to the .env file")
    p.add_argument("scope", help="Scope name to filter by (e.g. prod)")
    p.add_argument(
        "--separator",
        default="__",
        help="Separator between scope and key name (default: __)",
    )
    p.add_argument(
        "--keep-prefix",
        action="store_true",
        default=False,
        help="Do not strip the scope prefix from output key names",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="fmt",
        help="Output format (default: text)",
    )
    p.set_defaults(func=run_scope)


def run_scope(args: argparse.Namespace) -> int:
    try:
        env = parse_env_file(args.file)
    except EnvParseError as exc:
        print(f"Parse error: {exc}", file=sys.stderr)
        return 1

    try:
        result = scope_env(
            env,
            scope=args.scope,
            separator=args.separator,
            source=args.file,
            strip_prefix=not args.keep_prefix,
        )
    except ScopeError as exc:
        print(f"Scope error: {exc}", file=sys.stderr)
        return 1

    if args.fmt == "json":
        print(json.dumps(result.as_dict(), indent=2))
        return 0

    _print_text(result)
    return 0


def _print_text(result) -> None:  # type: ignore[type-arg]
    if result.is_empty:
        print(f"No keys found for scope '{result.scope}' in {result.source}")
        return

    print(f"Scope '{result.scope}' — {result.total_keys} key(s) from {result.source}")
    print("-" * 50)
    for sk in result.keys:
        print(f"  {sk.key}={sk.value}")
