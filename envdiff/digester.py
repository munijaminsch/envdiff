"""Compute a deterministic hash/digest of an env file's contents."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Dict, Optional


class DigestError(Exception):
    """Raised when digesting fails."""


@dataclass
class DigestResult:
    source: str
    algorithm: str
    hex_digest: str
    key_count: int
    key_digests: Dict[str, str] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "source": self.source,
            "algorithm": self.algorithm,
            "hex_digest": self.hex_digest,
            "key_count": self.key_count,
            "key_digests": self.key_digests,
        }


def _hash(value: str, algorithm: str) -> str:
    h = hashlib.new(algorithm)
    h.update(value.encode())
    return h.hexdigest()


def digest_env(
    env: Dict[str, str],
    *,
    source: str = "",
    algorithm: str = "sha256",
) -> DigestResult:
    """Return a DigestResult for *env*.

    The overall digest is computed over the canonical JSON representation of
    the sorted key/value pairs so it is stable across Python versions.
    """
    if algorithm not in hashlib.algorithms_available:
        raise DigestError(f"Unsupported hash algorithm: {algorithm!r}")

    key_digests = {k: _hash(v, algorithm) for k, v in sorted(env.items())}

    canonical = json.dumps(
        {k: v for k, v in sorted(env.items())}, sort_keys=True, separators=(",", ":")
    )
    overall = _hash(canonical, algorithm)

    return DigestResult(
        source=source,
        algorithm=algorithm,
        hex_digest=overall,
        key_count=len(env),
        key_digests=key_digests,
    )


def compare_digests(
    left: DigestResult,
    right: DigestResult,
) -> Dict[str, Optional[str]]:
    """Return a mapping of keys whose digests differ between *left* and *right*.

    Keys present only in one side are included with ``None`` for the missing
    side's digest.
    """
    all_keys = set(left.key_digests) | set(right.key_digests)
    diffs: Dict[str, Optional[str]] = {}
    for key in sorted(all_keys):
        l_dig = left.key_digests.get(key)
        r_dig = right.key_digests.get(key)
        if l_dig != r_dig:
            diffs[key] = r_dig  # None when missing in right
    return diffs
