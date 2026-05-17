"""Generate a .env.template file from one or more parsed env dicts."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional


class TemplateError(Exception):
    """Raised when template generation fails."""


@dataclass
class TemplateResult:
    """Holds the generated template lines and metadata."""

    keys: List[str]
    placeholder: str
    _lines: List[str] = field(default_factory=list, repr=False)

    @property
    def content(self) -> str:
        return "\n".join(self._lines) + "\n" if self._lines else ""

    @property
    def key_count(self) -> int:
        return len(self.keys)

    def as_dict(self) -> dict:
        return {
            "key_count": self.key_count,
            "placeholder": self.placeholder,
            "keys": self.keys,
        }


def build_template(
    envs: Iterable[Dict[str, str]],
    *,
    placeholder: str = "CHANGE_ME",
    sort_keys: bool = True,
    comment_header: Optional[str] = None,
) -> TemplateResult:
    """Merge keys from all *envs* and produce a template with blank/placeholder values.

    Args:
        envs: Iterable of parsed env dicts (key -> value).
        placeholder: Value written next to every key in the template.
        sort_keys: When True, keys are emitted in alphabetical order.
        comment_header: Optional comment block prepended to the template.

    Returns:
        A :class:`TemplateResult` with the generated content.

    Raises:
        TemplateError: If *placeholder* is an empty string.
    """
    if not placeholder:
        raise TemplateError("placeholder must not be empty")

    merged: dict[str, None] = {}
    for env in envs:
        if not isinstance(env, dict):
            raise TemplateError(f"expected dict, got {type(env).__name__}")
        merged.update({k: None for k in env})

    keys = sorted(merged) if sort_keys else list(merged)

    lines: list[str] = []
    if comment_header:
        for line in comment_header.splitlines():
            lines.append(f"# {line}" if not line.startswith("#") else line)
        lines.append("")

    for key in keys:
        lines.append(f"{key}={placeholder}")

    return TemplateResult(keys=keys, placeholder=placeholder, _lines=lines)


def write_template(result: TemplateResult, path: Path) -> None:
    """Write *result* content to *path*, creating parent directories as needed."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(result.content, encoding="utf-8")
    except OSError as exc:
        raise TemplateError(f"could not write template to {path}: {exc}") from exc
