"""Encode a parsed env dict into various string formats (.env, JSON, TOML-style)."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Dict, Literal

EncodeFormat = Literal["dotenv", "json", "toml"]


class EncodeError(Exception):
    """Raised when encoding fails."""


@dataclass
class EncodeResult:
    source: str
    fmt: EncodeFormat
    content: str
    key_count: int

    def as_dict(self) -> Dict[str, object]:
        return {
            "source": self.source,
            "format": self.fmt,
            "key_count": self.key_count,
            "content": self.content,
        }


def _encode_dotenv(env: Dict[str, str]) -> str:
    lines = []
    for key in sorted(env):
        value = env[key]
        if any(ch in value for ch in (" ", "\t", "#", '"', "'")):
            value = f'"{value}"'
        lines.append(f"{key}={value}")
    return "\n".join(lines) + ("\n" if lines else "")


def _encode_json(env: Dict[str, str]) -> str:
    return json.dumps(dict(sorted(env.items())), indent=2) + "\n"


def _encode_toml(env: Dict[str, str]) -> str:
    lines = []
    for key in sorted(env):
        value = env[key].replace("\\", "\\\\").replace('"', '\\"')
        lines.append(f'{key} = "{value}"')
    return "\n".join(lines) + ("\n" if lines else "")


def encode_env(
    env: Dict[str, str],
    fmt: EncodeFormat = "dotenv",
    source: str = "<unknown>",
) -> EncodeResult:
    """Encode *env* into the requested string format."""
    if not isinstance(env, dict):
        raise EncodeError("env must be a dict")
    if fmt == "dotenv":
        content = _encode_dotenv(env)
    elif fmt == "json":
        content = _encode_json(env)
    elif fmt == "toml":
        content = _encode_toml(env)
    else:
        raise EncodeError(f"Unknown format: {fmt!r}")
    return EncodeResult(source=source, fmt=fmt, content=content, key_count=len(env))
