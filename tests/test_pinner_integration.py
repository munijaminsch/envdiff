"""Integration tests for pinner: parse a real .env file then pin it."""
import pathlib
import pytest

from envdiff.parser import parse_env_file
from envdiff.pinner import pin_env, PinResult


@pytest.fixture()
def env_dir(tmp_path: pathlib.Path) -> pathlib.Path:
    return tmp_path


def _write(directory: pathlib.Path, name: str, content: str) -> pathlib.Path:
    p = directory / name
    p.write_text(content)
    return p


def test_pin_parsed_file_all_match(env_dir):
    p = _write(env_dir, ".env", "HOST=localhost\nPORT=5432\n")
    env = parse_env_file(p)
    result = pin_env(env, {"HOST": "localhost", "PORT": "5432"}, source=str(p))
    assert isinstance(result, PinResult)
    assert result.is_clean
    assert result.drift_count == 0


def test_pin_detects_drift_after_parse(env_dir):
    p = _write(env_dir, ".env", "HOST=remotehost\nPORT=5432\n")
    env = parse_env_file(p)
    result = pin_env(env, {"HOST": "localhost", "PORT": "5432"}, source=str(p))
    assert not result.is_clean
    assert result.drift_count == 1
    drifted = [e for e in result.entries if not e.is_pinned]
    assert drifted[0].key == "HOST"


def test_comments_not_included_after_parse(env_dir):
    p = _write(env_dir, ".env", "# comment\nAPP=myapp\n")
    env = parse_env_file(p)
    result = pin_env(env, {"APP": "myapp"})
    assert result.total_keys == 1
    assert result.is_clean


def test_missing_key_surfaces_as_drift(env_dir):
    p = _write(env_dir, ".env", "APP=myapp\n")
    env = parse_env_file(p)
    result = pin_env(env, {"APP": "myapp", "SECRET": "topsecret"})
    assert not result.is_clean
    missing = [e for e in result.entries if e.is_missing]
    assert len(missing) == 1
    assert missing[0].key == "SECRET"
