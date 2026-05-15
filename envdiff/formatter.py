"""Formatters for rendering CompareResult output."""

from __future__ import annotations

from typing import Protocol

from envdiff.comparator import CompareResult


class Formatter(Protocol):
    def format(self, result: CompareResult, env_names: tuple[str, str]) -> str:
        ...


class TextFormatter:
    """Renders a CompareResult as human-readable plain text."""

    _TICK = "\u2713"
    _CROSS = "\u2717"

    def format(self, result: CompareResult, env_names: tuple[str, str]) -> str:
        left, right = env_names
        lines: list[str] = []

        if not result.has_differences():
            lines.append(f"{self._TICK} No differences found between '{left}' and '{right}'.")
            return "\n".join(lines)

        lines.append(f"Comparing '{left}' <-> '{right}'")
        lines.append("-" * 40)

        for key in sorted(result.missing_in_right):
            lines.append(f"  {self._CROSS} MISSING IN {right.upper():<20} {key}")

        for key in sorted(result.missing_in_left):
            lines.append(f"  {self._CROSS} MISSING IN {left.upper():<20} {key}")

        for diff in sorted(result.value_mismatches, key=lambda d: d.key):
            lines.append(f"  ~ MISMATCH                        {diff.key}")
            lines.append(f"      {left}: {diff.left_value!r}")
            lines.append(f"      {right}: {diff.right_value!r}")

        lines.append("-" * 40)
        total = (
            len(result.missing_in_left)
            + len(result.missing_in_right)
            + len(result.value_mismatches)
        )
        lines.append(f"{total} issue(s) found.")
        return "\n".join(lines)


class JsonFormatter:
    """Renders a CompareResult as a JSON string."""

    def format(self, result: CompareResult, env_names: tuple[str, str]) -> str:
        import json

        left, right = env_names
        payload = {
            "left": left,
            "right": right,
            "missing_in_left": sorted(result.missing_in_left),
            "missing_in_right": sorted(result.missing_in_right),
            "value_mismatches": [
                {
                    "key": d.key,
                    "left_value": d.left_value,
                    "right_value": d.right_value,
                }
                for d in sorted(result.value_mismatches, key=lambda d: d.key)
            ],
            "has_differences": result.has_differences(),
        }
        return json.dumps(payload, indent=2)


def get_formatter(fmt: str) -> TextFormatter | JsonFormatter:
    """Return a formatter instance by name ('text' or 'json')."""
    if fmt == "json":
        return JsonFormatter()
    if fmt == "text":
        return TextFormatter()
    raise ValueError(f"Unknown formatter: {fmt!r}. Choose 'text' or 'json'.")
