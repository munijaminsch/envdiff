"""CLI sub-command: rename keys in an env file."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from envdiff.parser import parse_env_file
from envdiff.renamer import RenameError, rename_keys


def add_rename_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "rename",
        help="Rename keys in an .env file and write the result.",
    )
    p.add_argument("file", help="Path to the .env file to process.")
    p.add_argument(
        "--map",
        metavar="OLD=NEW",
        action="append",
        required=True,
        dest="mappings",
        help="Key rename in OLD=NEW format. May be repeated.",
    )
    p.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="Allow renaming onto an already-existing target key.",
    )
    p.add_argument(
        "--output",
        metavar="FILE",
        default=None,
        help="Write result to FILE instead of stdout.",
    )
    p.add_argument(
        "--json",
        action="store_true",
        default=False,
        dest="as_json",
        help="Print a JSON summary instead of env-file format.",
    )
    p.set_defaults(func=run_rename)


def _parse_mapping(raw: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for item in raw:
        if "=" not in item:
            raise ValueError(f"Invalid --map value (expected OLD=NEW): {item!r}")
        old, new = item.split("=", 1)
        result[old.strip()] = new.strip()
    return result


def run_rename(args: argparse.Namespace) -> int:
    try:
        env = parse_env_file(Path(args.file))
        mapping = _parse_mapping(args.mappings)
        result = rename_keys(env, mapping, overwrite=args.overwrite)
    except (RenameError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.as_json:
        output = json.dumps(result.as_dict(), indent=2)
    else:
        lines = [f"{k}={v}" for k, v in sorted(result.renamed.items())]
        output = "\n".join(lines)

    if args.output:
        Path(args.output).write_text(output + "\n", encoding="utf-8")
        print(f"Written to {args.output}")
        if result.skipped_count:
            print(f"Skipped {result.skipped_count} rename(s).", file=sys.stderr)
    else:
        print(output)

    return 0
