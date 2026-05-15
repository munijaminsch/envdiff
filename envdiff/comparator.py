"""Compare parsed .env file dictionaries and report differences."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class KeyDiff:
    """Represents a single key difference between two environments."""

    key: str
    status: str  # 'missing_in_left', 'missing_in_right', 'value_mismatch'
    left_value: Optional[str] = None
    right_value: Optional[str] = None

    def __str__(self) -> str:
        if self.status == "missing_in_left":
            return f"  - [{self.key}] missing in left (right={self.right_value!r})"
        if self.status == "missing_in_right":
            return f"  - [{self.key}] missing in right (left={self.left_value!r})"
        return (
            f"  - [{self.key}] value mismatch "
            f"(left={self.left_value!r}, right={self.right_value!r})"
        )


@dataclass
class CompareResult:
    """Aggregated result of comparing two .env files."""

    left_name: str
    right_name: str
    diffs: List[KeyDiff] = field(default_factory=list)

    @property
    def has_differences(self) -> bool:
        return len(self.diffs) > 0

    @property
    def missing_in_left(self) -> List[KeyDiff]:
        return [d for d in self.diffs if d.status == "missing_in_left"]

    @property
    def missing_in_right(self) -> List[KeyDiff]:
        return [d for d in self.diffs if d.status == "missing_in_right"]

    @property
    def mismatched(self) -> List[KeyDiff]:
        return [d for d in self.diffs if d.status == "value_mismatch"]

    def summary(self) -> str:
        lines = [
            f"Comparing '{self.left_name}' vs '{self.right_name}'",
            f"  Missing in left  : {len(self.missing_in_left)}",
            f"  Missing in right : {len(self.missing_in_right)}",
            f"  Value mismatches : {len(self.mismatched)}",
        ]
        if self.diffs:
            lines.append("Details:")
            lines.extend(str(d) for d in self.diffs)
        else:
            lines.append("No differences found.")
        return "\n".join(lines)


def compare_envs(
    left: Dict[str, str],
    right: Dict[str, str],
    left_name: str = "left",
    right_name: str = "right",
) -> CompareResult:
    """Compare two env dictionaries and return a CompareResult."""
    result = CompareResult(left_name=left_name, right_name=right_name)

    all_keys = sorted(set(left) | set(right))

    for key in all_keys:
        in_left = key in left
        in_right = key in right

        if in_left and not in_right:
            result.diffs.append(
                KeyDiff(key=key, status="missing_in_right", left_value=left[key])
            )
        elif in_right and not in_left:
            result.diffs.append(
                KeyDiff(key=key, status="missing_in_left", right_value=right[key])
            )
        elif left[key] != right[key]:
            result.diffs.append(
                KeyDiff(
                    key=key,
                    status="value_mismatch",
                    left_value=left[key],
                    right_value=right[key],
                )
            )

    return result
