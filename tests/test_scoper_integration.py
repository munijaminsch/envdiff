"""Integration tests: parse a real .env file then scope it."""
import pathlib
import pytest

from envdiff.parser import parse_env_file
from envdiff.scoper import scope_env


@pytest.fixture()
def env_dir(tmp_path: pathlib.Path) -> pathlib.Path:
    return tmp_path


def _write(path: pathlib.Path, content: str) -> pathlib.Path:
    path.write_text(content)
    return path


def test_scope_parsed_file(env_dir):
    f = _write(
        env_dir / "multi.env",
        "PROD__DB=postgres\nDEV__DB=sqlite\nPROD__PORT=5432\n",
    )
    env = parse_env_file(str(f))
    result = scope_env(env, scope="prod", source=str(f))
    assert result.total_keys == 2
    assert result.source == str(f)


def test_scoped_keys_have_correct_values(env_dir):
    f = _write(
        env_dir / "scoped.env",
        'PROD__API_KEY="secret-prod"\nDEV__API_KEY="secret-dev"\n',
    )
    env = parse_env_file(str(f))
    result = scope_env(env, scope="prod")
    assert result.total_keys == 1
    assert result.keys[0].value == "secret-prod"


def test_comments_not_included_after_parse(env_dir):
    f = _write(
        env_dir / "commented.env",
        "# PROD__IGNORED=yes\nPROD__REAL=yes\n",
    )
    env = parse_env_file(str(f))
    result = scope_env(env, scope="prod")
    assert result.total_keys == 1
    assert result.keys[0].key == "REAL"


def test_as_dict_round_trip(env_dir):
    f = _write(env_dir / "rt.env", "PROD__X=1\nPROD__Y=2\n")
    env = parse_env_file(str(f))
    d = scope_env(env, scope="prod", source="rt.env").as_dict()
    assert d["total_keys"] == 2
    key_names = {entry["key"] for entry in d["keys"]}
    assert key_names == {"X", "Y"}
