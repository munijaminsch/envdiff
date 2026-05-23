"""CLI sub-command: envdiff chain — diff several file pairs in sequence."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List

from envdiff.comparator import compare
from envdiff.comparator_chain import build_chain
from envdiff.parser import parse_env_file


def add_chain_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "chain",
        help="Diff multiple pairs of .env files sequentially.",
    )
    p.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help="Even number of files: left1 right1 left2 right2 …",
    )
    p.add_argument(
        "--json",
        dest="as_json",
        action="store_true",
        default=False,
        help="Output results as JSON.",
    )
    p.add_argument(
        "--fail-on-diff",
        dest="fail_on_diff",
        action="store_true",
        default=False,
        help="Exit with code 1 if any pair has differences.",
    )


def run_chain(args: argparse.Namespace) -> int:
    files: List[str] = args.files
    if len(files) % 2 != 0:
        print("error: 'chain' requires an even number of files.", file=sys.stderr)
        return 2

    pairs = []
    for i in range(0, len(files), 2):
        left_path, right_path = files[i], files[i + 1]
        try:
            left_env = parse_env_file(left_path)
            right_env = parse_env_file(right_path)
        except Exception as exc:  # noqa: BLE001
            print(f"error: {exc}", file=sys.stderr)
            return 2
        result = compare(left_env, right_env, left_name=left_path, right_name=right_path)
        pairs.append((left_path, right_path, result))

    chain = build_chain(pairs)

    if args.as_json:
        print(json.dumps(chain.as_dict(), indent=2))
    else:
        _print_text(chain)

    if args.fail_on_diff and not chain.is_clean():
        return 1
    return 0


def _print_text(chain) -> None:  # type: ignore[no-untyped-def]
    print(f"Pairs checked : {chain.total_pairs}")
    print(f"Clean         : {chain.clean_pairs}")
    print(f"Dirty         : {chain.dirty_pairs}")
    for entry in chain.entries:
        status = "OK" if not entry.result.has_differences() else "DIFF"
        print(f"  [{status}] {entry.left} <-> {entry.right}")
        if entry.result.has_differences():
            for key in entry.result.missing_in_right():
                print(f"       missing in right : {key}")
            for key in entry.result.missing_in_left():
                print(f"       missing in left  : {key}")
            for diff in entry.result.value_mismatches():
                print(f"       mismatch         : {diff.key} ({diff.left_value!r} != {diff.right_value!r})")
