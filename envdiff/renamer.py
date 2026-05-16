"""Rename keys across a parsed env mapping."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple


class RenameError(Exception):
    """Raised when a rename operation cannot be completed."""


@dataclass
class RenameResult:
    """Holds the outcome of a rename operation."""

    original: Dict[str, str]
    renamed: Dict[str, str]
    applied: List[Tuple[str, str]] = field(default_factory=list)
    skipped: List[Tuple[str, str]] = field(default_factory=list)

    @property
    def applied_count(self) -> int:
        return len(self.applied)

    @property
    def skipped_count(self) -> int:
        return len(self.skipped)

    def as_dict(self) -> dict:
        return {
            "renamed": self.renamed,
            "applied": [{"from": f, "to": t} for f, t in self.applied],
            "skipped": [{"from": f, "to": t} for f, t in self.skipped],
            "applied_count": self.applied_count,
            "skipped_count": self.skipped_count,
        }


def rename_keys(
    env: Dict[str, str],
    mapping: Dict[str, str],
    *,
    overwrite: bool = False,
) -> RenameResult:
    """Rename keys in *env* according to *mapping* (old_name -> new_name).

    Parameters
    ----------
    env:
        Source key/value pairs.
    mapping:
        Dictionary whose keys are existing key names and values are the
        desired new names.
    overwrite:
        When *True*, rename even if the target key already exists in *env*.
        When *False* (default), skip renames that would overwrite an existing
        key and record them in ``RenameResult.skipped``.

    Raises
    ------
    RenameError
        If *mapping* contains duplicate target names.
    """
    targets = list(mapping.values())
    if len(targets) != len(set(targets)):
        raise RenameError("Rename mapping contains duplicate target key names.")

    result: Dict[str, str] = dict(env)
    applied: List[Tuple[str, str]] = []
    skipped: List[Tuple[str, str]] = []

    for old, new in mapping.items():
        if old not in result:
            skipped.append((old, new))
            continue
        if new in result and not overwrite:
            skipped.append((old, new))
            continue
        value = result.pop(old)
        result[new] = value
        applied.append((old, new))

    return RenameResult(
        original=dict(env),
        renamed=result,
        applied=applied,
        skipped=skipped,
    )
