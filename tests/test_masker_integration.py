"""Integration tests for masker — parse a real .env file then mask it."""
import pathlib
import pytest

from envdiff.parser import parse_env_file
from envdiff.masker import mask_env


@pytest.fixture()
def env_dir(tmp_path: pathlib.Path) -> pathlib.Path:
    return tmp_path


def _write(directory: pathlib.Path, name: str, content: str) -> pathlib.Path:
    p = directory / name
    p.write_text(content)
    return p


def test_mask_parsed_file(env_dir):
    p = _write(
        env_dir,
        ".env",
        "DB_PASSWORD=supersecret\nAPP_NAME=myapp\nAPI_KEY=abc123\n",
    )
    env = parse_env_file(str(p))
    result = mask_env(env, source=str(p))

    assert result.total_keys == 3
    by_key = {e.key: e for e in result.entries}
    assert by_key["DB_PASSWORD"].masked_value == "***********"
    assert by_key["APP_NAME"].masked_value == "*****"
    assert by_key["API_KEY"].masked_value == "******"


def test_mask_only_sensitive_keys(env_dir):
    p = _write(
        env_dir,
        ".env",
        "SECRET=topsecret\nPORT=8080\nDEBUG=true\n",
    )
    env = parse_env_file(str(p))
    result = mask_env(env, source=str(p), keys=["SECRET"])

    by_key = {e.key: e for e in result.entries}
    assert by_key["SECRET"].masked_value == "*********"
    assert by_key["PORT"].masked_value == "8080"
    assert by_key["DEBUG"].masked_value == "true"


def test_mask_with_visible_chars(env_dir):
    p = _write(env_dir, ".env", "TOKEN=abcdef1234\n")
    env = parse_env_file(str(p))
    result = mask_env(env, source=str(p), visible=4)

    entry = result.entries[0]
    assert entry.masked_value.endswith("1234")
    assert entry.masked_value == "******1234"


def test_empty_values_in_file(env_dir):
    p = _write(env_dir, ".env", "EMPTY=\nFILLED=yes\n")
    env = parse_env_file(str(p))
    result = mask_env(env, source=str(p))

    by_key = {e.key: e for e in result.entries}
    assert by_key["EMPTY"].was_empty is True
    assert by_key["EMPTY"].masked_value == ""
    assert by_key["FILLED"].was_empty is False
