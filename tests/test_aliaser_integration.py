"""Integration tests: parse a real .env file then apply aliases."""
import pathlib
import pytest

from envdiff.parser import parse_env_file
from envdiff.aliaser import apply_aliases, AliasError


@pytest.fixture()
def env_dir(tmp_path: pathlib.Path) -> pathlib.Path:
    return tmp_path


def _write(directory: pathlib.Path, name: str, content: str) -> pathlib.Path:
    p = directory / name
    p.write_text(content)
    return p


def test_alias_parsed_file(env_dir):
    p = _write(env_dir, ".env", "DB_HOST=localhost\nDB_PORT=5432\nSECRET=abc\n")
    env = parse_env_file(str(p))
    mapping = {"DB_HOST": "database_host", "DB_PORT": "database_port"}
    result = apply_aliases(env, mapping, source=str(p))
    assert result.mapped_count == 2
    assert result.unmapped_count == 1
    assert "SECRET" in result.unmapped


def test_all_keys_mapped_is_clean(env_dir):
    p = _write(env_dir, ".env", "API_KEY=xyz\nAPI_SECRET=secret\n")
    env = parse_env_file(str(p))
    mapping = {"API_KEY": "api_key", "API_SECRET": "api_secret"}
    result = apply_aliases(env, mapping, source=str(p))
    assert result.is_clean


def test_comments_not_included_after_parse(env_dir):
    p = _write(env_dir, ".env", "# comment\nFOO=bar\n")
    env = parse_env_file(str(p))
    result = apply_aliases(env, {"FOO": "foo_alias"}, source=str(p))
    # comments are stripped by parser; only FOO should be present
    assert result.total_keys == 1
    assert result.is_clean


def test_as_dict_round_trip(env_dir):
    p = _write(env_dir, ".env", "HOST=example.com\nPORT=443\n")
    env = parse_env_file(str(p))
    result = apply_aliases(env, {"HOST": "host", "PORT": "port"}, source=str(p))
    d = result.as_dict()
    assert d["mapped_count"] == 2
    aliases = {e["alias"] for e in d["mapped"]}
    assert aliases == {"host", "port"}
