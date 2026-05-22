"""Integration tests: parse a real .env file then encode it back."""
import json
import pathlib
import pytest

from envdiff.encoder import encode_env
from envdiff.parser import parse_env_file


@pytest.fixture()
def env_dir(tmp_path: pathlib.Path) -> pathlib.Path:
    return tmp_path


def _write(directory: pathlib.Path, name: str, text: str) -> pathlib.Path:
    p = directory / name
    p.write_text(text)
    return p


def test_parse_then_encode_dotenv_round_trip(env_dir):
    src = _write(env_dir, "app.env", "HOST=localhost\nPORT=5432\n")
    env = parse_env_file(src)
    result = encode_env(env, fmt="dotenv", source=str(src))
    assert "HOST=localhost" in result.content
    assert "PORT=5432" in result.content


def test_parse_then_encode_json_contains_all_keys(env_dir):
    src = _write(env_dir, "app.env", "DB=postgres\nDEBUG=true\n")
    env = parse_env_file(src)
    result = encode_env(env, fmt="json", source=str(src))
    parsed = json.loads(result.content)
    assert "DB" in parsed
    assert "DEBUG" in parsed


def test_comments_not_included_after_encode(env_dir):
    src = _write(env_dir, "app.env", "# comment\nKEY=val\n")
    env = parse_env_file(src)
    result = encode_env(env, fmt="dotenv")
    assert "#" not in result.content


def test_key_count_matches_parsed_keys(env_dir):
    src = _write(env_dir, "app.env", "A=1\nB=2\nC=3\n")
    env = parse_env_file(src)
    result = encode_env(env, fmt="toml")
    assert result.key_count == 3
