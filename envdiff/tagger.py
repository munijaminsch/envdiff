"""Tag keys in an env mapping with user-defined labels."""

from __future__ import annotations

from dataclasses import dataclass, field
from fnmatch import fnmatch
from typing import Dict, List, Mapping, Optional


class TagError(Exception):
    """Raised when tagging configuration is invalid."""


@dataclass
class KeyTag:
    key: str
    tags: List[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {"key": self.key, "tags": list(self.tags)}


@dataclass
class TagResult:
    source: str
    tagged: List[KeyTag] = field(default_factory=list)

    @property
    def total_keys(self) -> int:
        return len(self.tagged)

    def keys_with_tag(self, tag: str) -> List[str]:
        return [kt.key for kt in self.tagged if tag in kt.tags]

    def tags_for_key(self, key: str) -> Optional[List[str]]:
        for kt in self.tagged:
            if kt.key == key:
                return kt.tags
        return None

    def as_dict(self) -> dict:
        return {
            "source": self.source,
            "total_keys": self.total_keys,
            "tagged": [kt.as_dict() for kt in self.tagged],
        }


def tag_keys(
    env: Mapping[str, str],
    rules: Mapping[str, List[str]],
    source: str = "<env>",
) -> TagResult:
    """Apply tag rules to env keys.

    Args:
        env: A mapping of key -> value (e.g. parsed .env file).
        rules: A mapping of glob pattern -> list of tags to apply.
        source: Label for the origin of the env data.

    Returns:
        A TagResult containing each key and its matched tags.
    """
    if not isinstance(rules, Mapping):
        raise TagError("rules must be a mapping of pattern -> list of tags")

    for pattern, tags in rules.items():
        if not isinstance(tags, list):
            raise TagError(
                f"Tags for pattern '{pattern}' must be a list, got {type(tags).__name__}"
            )

    tagged: List[KeyTag] = []
    for key in env:
        matched_tags: List[str] = []
        for pattern, tags in rules.items():
            if fnmatch(key, pattern):
                for tag in tags:
                    if tag not in matched_tags:
                        matched_tags.append(tag)
        tagged.append(KeyTag(key=key, tags=matched_tags))

    return TagResult(source=source, tagged=tagged)
