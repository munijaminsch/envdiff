"""masker.py — Mask env values by replacing characters with a fixed symbol."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


class MaskError(Exception):
    """Raised when masking fails."""


_DEFAULT_SYMBOL = "*"
_DEFAULT_VISIBLE = 0


@dataclass
class MaskedKey:
    key: str
    original_length: int
    masked_value: str
    was_empty: bool

    def as_dict(self) -> dict:
        return {
            "key": self.key,
            "original_length": self.original_length,
            "masked_value": self.masked_value,
            "was_empty": self.was_empty,
        }


@dataclass
class MaskResult:
    source: str
    entries: List[MaskedKey] = field(default_factory=list)

    @property
    def total_keys(self) -> int:
        return len(self.entries)

    @property
    def masked_count(self) -> int:
        return sum(1 for e in self.entries if not e.was_empty)

    def as_dict(self) -> dict:
        return {
            "source": self.source,
            "total_keys": self.total_keys,
            "masked_count": self.masked_count,
            "entries": [e.as_dict() for e in self.entries],
        }


def _mask_value(
    value: str,
    symbol: str = _DEFAULT_SYMBOL,
    visible: int = _DEFAULT_VISIBLE,
) -> str:
    """Replace characters with *symbol*, optionally keeping *visible* trailing chars."""
    if not value:
        return value
    if visible <= 0 or visible >= len(value):
        return symbol * len(value)
    return symbol * (len(value) - visible) + value[-visible:]


def mask_env(
    env: Dict[str, str],
    source: str = "",
    keys: Optional[List[str]] = None,
    symbol: str = _DEFAULT_SYMBOL,
    visible: int = _DEFAULT_VISIBLE,
) -> MaskResult:
    """Mask values in *env*.

    Args:
        env: Mapping of key → value.
        source: Label for the origin file.
        keys: If provided, only these keys are masked; others are passed through.
        symbol: Character used for masking (default ``*``).
        visible: Number of trailing characters to leave unmasked.
    """
    if len(symbol) != 1:
        raise MaskError("symbol must be exactly one character")
    if visible < 0:
        raise MaskError("visible must be >= 0")

    target_keys = set(keys) if keys is not None else None
    result = MaskResult(source=source)

    for key, value in env.items():
        should_mask = target_keys is None or key in target_keys
        if should_mask:
            masked = _mask_value(value, symbol=symbol, visible=visible)
        else:
            masked = value
        result.entries.append(
            MaskedKey(
                key=key,
                original_length=len(value),
                masked_value=masked,
                was_empty=(value == ""),
            )
        )

    return result
