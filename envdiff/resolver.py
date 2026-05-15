"""Resolve .env files from a directory or explicit paths."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from envdiff.parser import EnvParseError, parse_env_file


class ResolveError(Exception):
    """Raised when one or more env files cannot be resolved or parsed."""


def find_env_files(directory: str | Path) -> List[Path]:
    """Return all .env* files found directly inside *directory*.

    Files are returned sorted alphabetically so results are deterministic.
    Hidden files (e.g. ``.env``) and files like ``.env.production`` are both
    included.  Sub-directories are not traversed.
    """
    directory = Path(directory)
    if not directory.is_dir():
        raise ResolveError(f"Not a directory: {directory}")

    matches = sorted(
        p for p in directory.iterdir()
        if p.is_file() and p.name.startswith(".env")
    )
    return matches


def load_envs(
    paths: List[str | Path],
) -> Dict[str, Dict[str, Optional[str]]]:
    """Parse each path and return a mapping of *filename -> key/value dict*.

    Raises :class:`ResolveError` if any file cannot be read or parsed.
    """
    result: Dict[str, Dict[str, Optional[str]]] = {}
    errors: List[str] = []

    for raw_path in paths:
        path = Path(raw_path)
        try:
            result[path.name] = parse_env_file(str(path))
        except FileNotFoundError:
            errors.append(f"File not found: {path}")
        except EnvParseError as exc:
            errors.append(f"Parse error in {path}: {exc}")

    if errors:
        raise ResolveError("\n".join(errors))

    return result


def resolve_pair(
    left: str | Path,
    right: str | Path,
) -> Tuple[Dict[str, Optional[str]], Dict[str, Optional[str]]]:
    """Convenience helper: load exactly two env files and return their dicts.

    Returns a ``(left_dict, right_dict)`` tuple.
    """
    loaded = load_envs([left, right])
    left_name = Path(left).name
    right_name = Path(right).name
    return loaded[left_name], loaded[right_name]
