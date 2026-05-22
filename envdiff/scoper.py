"""Scope filtering: restrict env keys to a named environment scope."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


class ScopeError(Exception):
    """Raised when scoping fails."""


@dataclass
class ScopedKey:
    key: str
    value: str
    scope: str

    def as_dict(self) -> dict:
        return {"key": self.key, "value": self.value, "scope": self.scope}


@dataclass
class ScopeResult:
    source: str
    scope: str
    keys: List[ScopedKey] = field(default_factory=list)

    @property
    def total_keys(self) -> int:
        return len(self.keys)

    @property
    def is_empty(self) -> bool:
        return self.total_keys == 0

    def as_dict(self) -> dict:
        return {
            "source": self.source,
            "scope": self.scope,
            "total_keys": self.total_keys,
            "keys": [k.as_dict() for k in self.keys],
        }


def scope_env(
    env: Dict[str, str],
    scope: str,
    *,
    separator: str = "__",
    source: str = "<env>",
    strip_prefix: bool = True,
) -> ScopeResult:
    """Return only keys that belong to *scope*.

    A key belongs to a scope when it starts with ``<SCOPE><separator>``
    (case-insensitive prefix match).

    Args:
        env: Parsed key/value mapping.
        scope: The scope name to filter by (e.g. ``"prod"``).
        separator: Token that separates scope from key name. Default ``"__"``.
        source: Label stored in the result for traceability.
        strip_prefix: When *True* (default) the scope prefix is removed from
            the key names stored in the result.

    Returns:
        :class:`ScopeResult` containing only the matching keys.

    Raises:
        :class:`ScopeError`: If *scope* is empty or *separator* is empty.
    """
    if not scope:
        raise ScopeError("scope must not be empty")
    if not separator:
        raise ScopeError("separator must not be empty")

    prefix = scope.upper() + separator
    matched: List[ScopedKey] = []

    for raw_key, value in env.items():
        if raw_key.upper().startswith(prefix.upper()):
            stored_key = raw_key[len(prefix):] if strip_prefix else raw_key
            matched.append(ScopedKey(key=stored_key, value=value, scope=scope))

    return ScopeResult(source=source, scope=scope, keys=matched)
