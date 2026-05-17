"""Patch an env file by applying a dict of key->value updates."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


class PatchError(Exception):
    """Raised when patching fails."""


@dataclass
class PatchResult:
    """Result of patching an env file."""

    source: str
    updated: Dict[str, str] = field(default_factory=dict)
    added: Dict[str, str] = field(default_factory=dict)
    content: str = ""

    @property
    def changed_count(self) -> int:
        return len(self.updated)

    @property
    def added_count(self) -> int:
        return len(self.added)

    def as_dict(self) -> dict:
        return {
            "source": self.source,
            "changed_count": self.changed_count,
            "added_count": self.added_count,
            "updated": self.updated,
            "added": self.added,
        }


_KEY_RE = re.compile(r'^([A-Za-z_][A-Za-z0-9_]*)\s*=')


def patch_env(source: str, patches: Dict[str, str], add_missing: bool = True) -> PatchResult:
    """Apply *patches* to *source* env text and return a PatchResult.

    Args:
        source: Raw text content of an env file.
        patches: Mapping of key -> new value to apply.
        add_missing: When True, keys not present in source are appended.
    """
    if not isinstance(patches, dict):
        raise PatchError("patches must be a dict")

    remaining = dict(patches)
    updated: Dict[str, str] = {}
    lines: List[str] = []

    for line in source.splitlines(keepends=True):
        m = _KEY_RE.match(line)
        if m:
            key = m.group(1)
            if key in remaining:
                new_val = remaining.pop(key)
                lines.append(f"{key}={new_val}\n")
                updated[key] = new_val
                continue
        lines.append(line)

    added: Dict[str, str] = {}
    if add_missing and remaining:
        if lines and not lines[-1].endswith("\n"):
            lines.append("\n")
        for key, val in remaining.items():
            lines.append(f"{key}={val}\n")
            added[key] = val

    return PatchResult(
        source="<string>",
        updated=updated,
        added=added,
        content="".join(lines),
    )


def patch_env_file(
    path: Path,
    patches: Dict[str, str],
    add_missing: bool = True,
    write: bool = False,
) -> PatchResult:
    """Patch an env file on disk."""
    path = Path(path)
    if not path.exists():
        raise PatchError(f"File not found: {path}")
    source_text = path.read_text(encoding="utf-8")
    result = patch_env(source_text, patches, add_missing=add_missing)
    result.source = str(path)
    if write:
        path.write_text(result.content, encoding="utf-8")
    return result
