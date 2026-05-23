"""Integration tests: parse a real .env file then digest it."""
import pathlib
import pytest

from envdiff.parser import parse_env_file
from envdiff.digester import digest_env, compare_digests


@pytest.fixture()
def env_dir(tmp_path: pathlib.Path):
    return tmp_path


def _write(directory: pathlib.Path, name: str, content: str) -> pathlib.Path:
    p = directory / name
    p.write_text(content)
    return p


def test_digest_parsed_file(env_dir):
    p = _write(env_dir, "prod.env", "APP_KEY=secret\nDEBUG=false\n")
    env = parse_env_file(p)
    result = digest_env(env, source=str(p))
    assert result.key_count == 2
    assert result.hex_digest
    assert "APP_KEY" in result.key_digests
    assert "DEBUG" in result.key_digests


def test_comments_not_included_in_digest(env_dir):
    p1 = _write(env_dir, "a.env", "KEY=val\n")
    p2 = _write(env_dir, "b.env", "# comment\nKEY=val\n")
    env1 = parse_env_file(p1)
    env2 = parse_env_file(p2)
    r1 = digest_env(env1)
    r2 = digest_env(env2)
    # Comments are stripped by the parser; digests must be identical.
    assert r1.hex_digest == r2.hex_digest


def test_digest_drift_detected_after_edit(env_dir):
    p = _write(env_dir, "app.env", "TOKEN=abc\nPORT=8080\n")
    original = digest_env(parse_env_file(p), source=str(p))

    # Simulate a value change.
    p.write_text("TOKEN=xyz\nPORT=8080\n")
    updated = digest_env(parse_env_file(p), source=str(p))

    assert original.hex_digest != updated.hex_digest
    diffs = compare_digests(original, updated)
    assert "TOKEN" in diffs
    assert "PORT" not in diffs


def test_as_dict_round_trip(env_dir):
    p = _write(env_dir, "env.env", "A=1\nB=2\n")
    result = digest_env(parse_env_file(p), source="env.env")
    d = result.as_dict()
    assert d["source"] == "env.env"
    assert d["key_count"] == 2
    assert isinstance(d["key_digests"], dict)
