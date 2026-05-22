"""Multi-file diff: compare more than two .env files simultaneously."""
from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations
from typing import Dict, List, Optional

from envdiff.comparator import CompareResult, compare
from envdiff.parser import parse_env_file


class MultiDiffError(Exception):
    """Raised when a multi-file diff cannot be completed."""


@dataclass
class PairDiff:
    left: str
    right: str
    result: CompareResult

    def as_dict(self) -> dict:
        return {
            "left": self.left,
            "right": self.right,
            "missing_in_right": [k for k in self.result.missing_in_right()],
            "missing_in_left": [k for k in self.result.missing_in_left()],
            "mismatched": [k for k in self.result.mismatched_keys()],
        }


@dataclass
class MultiDiffResult:
    sources: List[str]
    pairs: List[PairDiff] = field(default_factory=list)

    def is_clean(self) -> bool:
        return all(not p.result.has_differences() for p in self.pairs)

    def total_pairs(self) -> int:
        return len(self.pairs)

    def as_dict(self) -> dict:
        return {
            "sources": self.sources,
            "total_pairs": self.total_pairs(),
            "is_clean": self.is_clean(),
            "pairs": [p.as_dict() for p in self.pairs],
        }


def diff_multi(paths: List[str]) -> MultiDiffResult:
    """Compare every pair of env files from *paths*."""
    if len(paths) < 2:
        raise MultiDiffError("At least two files are required for a multi-diff.")

    envs: Dict[str, dict] = {}
    for path in paths:
        try:
            envs[path] = parse_env_file(path)
        except Exception as exc:
            raise MultiDiffError(f"Failed to parse '{path}': {exc}") from exc

    result = MultiDiffResult(sources=list(paths))
    for left, right in combinations(paths, 2):
        cmp = compare(envs[left], envs[right], left_name=left, right_name=right)
        result.pairs.append(PairDiff(left=left, right=right, result=cmp))

    return result
