"""CLI sub-command: envdiff merge — merge multiple .env files."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import List

from envdiff.merger import MergeError, merge_envs
from envdiff.parser import EnvParseError, parse_env_file


def _load_files(
    paths: List[Path],
) -> List[tuple]:
    """Parse each path and return list of (name, dict) tuples."""
    result = []
    for p in paths:
        try:
            env = parse_env_file(p)
        except EnvParseError as exc:
            print(f"[error] Cannot parse {p}: {exc}", file=sys.stderr)
            sys.exit(2)
        result.append((p.name, env))
    return result


def run_merge(args) -> int:  # noqa: ANN001
    """Execute the merge sub-command.  Returns exit code."""
    paths = [Path(f) for f in args.files]

    for p in paths:
        if not p.exists():
            print(f"[error] File not found: {p}", file=sys.stderr)
            return 2

    named_envs = _load_files(paths)

    try:
        result = merge_envs(named_envs, strategy=args.strategy)
    except MergeError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1

    if args.format == "json":
        output = {
            "merged": result.merged,
            "conflicts": [
                {"key": c.key, "values": c.values}
                for c in result.conflicts
            ],
            "sources": result.sources,
        }
        print(json.dumps(output, indent=2))
    else:
        for key, value in sorted(result.merged.items()):
            print(f"{key}={value}" if value is not None else f"{key}=")
        if result.has_conflicts and not args.quiet:
            print(
                f"\n# {len(result.conflicts)} conflict(s) detected:",
                file=sys.stderr,
            )
            for conflict in result.conflicts:
                print(f"#   {conflict}", file=sys.stderr)

    return 1 if (result.has_conflicts and args.fail_on_conflict) else 0


def add_merge_subparser(subparsers) -> None:  # noqa: ANN001
    """Register the 'merge' sub-command on an argparse subparsers object."""
    p = subparsers.add_parser(
        "merge",
        help="Merge multiple .env files into a unified baseline.",
    )
    p.add_argument("files", nargs="+", metavar="FILE", help=".env files to merge")
    p.add_argument(
        "--strategy",
        choices=("first", "last", "error"),
        default="first",
        help="Conflict resolution strategy (default: first)",
    )
    p.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format (default: text)",
    )
    p.add_argument(
        "--fail-on-conflict",
        action="store_true",
        default=False,
        help="Exit with code 1 when conflicts are detected.",
    )
    p.add_argument(
        "--quiet",
        action="store_true",
        default=False,
        help="Suppress conflict warnings on stderr.",
    )
    p.set_defaults(func=run_merge)
