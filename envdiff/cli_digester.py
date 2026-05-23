"""CLI sub-command: digest — show a stable hash for one or two .env files."""
from __future__ import annotations

import json
import sys
from argparse import ArgumentParser, Namespace
from typing import List

from envdiff.digester import compare_digests, digest_env
from envdiff.parser import parse_env_file


def add_digest_subparser(subparsers) -> None:  # type: ignore[type-arg]
    p: ArgumentParser = subparsers.add_parser(
        "digest",
        help="Compute a stable hash for one or two .env files.",
    )
    p.add_argument("files", nargs="+", metavar="FILE", help=".env file(s) to digest")
    p.add_argument(
        "--algorithm", "-a", default="sha256", metavar="ALGO",
        help="Hash algorithm (default: sha256)",
    )
    p.add_argument(
        "--json", dest="use_json", action="store_true",
        help="Output as JSON",
    )
    p.set_defaults(func=run_digest)


def run_digest(args: Namespace) -> int:
    if len(args.files) > 2:
        print("digest: at most two files are supported", file=sys.stderr)
        return 2

    results = []
    for path in args.files:
        try:
            env = parse_env_file(path)
            result = digest_env(env, source=path, algorithm=args.algorithm)
            results.append(result)
        except Exception as exc:  # noqa: BLE001
            print(f"digest: {exc}", file=sys.stderr)
            return 1

    if args.use_json:
        if len(results) == 1:
            print(json.dumps(results[0].as_dict(), indent=2))
        else:
            diffs = compare_digests(results[0], results[1])
            payload = {
                "left": results[0].as_dict(),
                "right": results[1].as_dict(),
                "diffs": diffs,
            }
            print(json.dumps(payload, indent=2))
        return 0

    _print_text(results)
    return 0


def _print_text(results: List) -> None:
    for r in results:
        print(f"{r.source or '<stdin>'}")
        print(f"  algorithm : {r.algorithm}")
        print(f"  digest    : {r.hex_digest}")
        print(f"  keys      : {r.key_count}")

    if len(results) == 2:
        diffs = compare_digests(results[0], results[1])
        if diffs:
            print("\nChanged / missing keys:")
            for key, digest in diffs.items():
                status = "missing in right" if digest is None else "changed"
                print(f"  {key}: {status}")
        else:
            print("\nDigests match — no differences detected.")
