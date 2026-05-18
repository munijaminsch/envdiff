"""Integration tests for envdiff.caster with envdiff.parser."""

import pathlib
import pytest

from envdiff.parser import parse_env_file
from envdiff.caster import cast_env


@pytest.fixture()
def env_dir(tmp_path: pathlib.Path) -> pathlib.Path:
    return tmp_path


def _write(directory: pathlib.Path, name: str, content: str) -> pathlib.Path:
    p = directory / name
    p.write_text(content)
    return p


def test_cast_parsed_file(env_dir):
    p = _write(
        env_dir,
        ".env",
        "DEBUG=true\nPORT=8080\nHOST=localhost\nRATIO=0.75\n",
    )
    env = parse_env_file(str(p))
    result = cast_env(env, source=str(p))
    by_key = {e.key: e for e in result.entries}
    assert by_key["DEBUG"].cast_value is True
    assert by_key["PORT"].cast_value == 8080
    assert by_key["HOST"].cast_value == "localhost"
    assert abs(by_key["RATIO"].cast_value - 0.75) < 1e-9


def test_comments_not_included_in_cast(env_dir):
    p = _write(
        env_dir,
        ".env",
        "# this is a comment\nACTIVE=yes\n\nCOUNT=3\n",
    )
    env = parse_env_file(str(p))
    result = cast_env(env, source=str(p))
    keys = {e.key for e in result.entries}
    assert "#" not in " ".join(keys)
    assert "ACTIVE" in keys
    assert "COUNT" in keys


def test_as_dict_round_trip(env_dir):
    p = _write(env_dir, ".env", "ENABLED=1\nNAME=envdiff\n")
    env = parse_env_file(str(p))
    result = cast_env(env, source="test.env")
    d = result.as_dict()
    assert d["total_keys"] == len(env)
    for entry_dict in d["entries"]:
        assert "cast_type" in entry_dict
        assert "raw" in entry_dict
