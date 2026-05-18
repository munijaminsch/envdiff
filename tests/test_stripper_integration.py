"""Integration tests for stripper: parse real .env files then strip."""

import pathlib
import pytest

from envdiff.parser import parse_env_file
from envdiff.stripper import strip_keys


@pytest.fixture()
def env_dir(tmp_path: pathlib.Path) -> pathlib.Path:
    return tmp_path


def _write(directory: pathlib.Path, name: str, content: str) -> pathlib.Path:
    p = directory / name
    p.write_text(content)
    return p


def test_strip_parsed_file_removes_orphans(env_dir):
    source_file = _write(
        env_dir,
        "app.env",
        "DB_HOST=localhost\nDB_PORT=5432\nLEGACY_FLAG=true\n",
    )
    ref_file = _write(
        env_dir,
        "template.env",
        "DB_HOST=\nDB_PORT=\n",
    )
    env = parse_env_file(source_file)
    ref = parse_env_file(ref_file)
    result = strip_keys(env, ref, source=str(source_file), reference_name=str(ref_file))

    assert "DB_HOST" in result.kept
    assert "DB_PORT" in result.kept
    assert result.removed_count == 1
    assert result.removed[0].key == "LEGACY_FLAG"


def test_clean_file_produces_no_removals(env_dir):
    source_file = _write(env_dir, "clean.env", "A=1\nB=2\n")
    ref_file = _write(env_dir, "ref.env", "A=\nB=\nC=\n")
    env = parse_env_file(source_file)
    ref = parse_env_file(ref_file)
    result = strip_keys(env, ref)
    assert result.is_clean is True


def test_comments_not_included_after_parse(env_dir):
    source_file = _write(
        env_dir,
        "commented.env",
        "# this is a comment\nVALID=yes\nORPHAN=no\n",
    )
    ref_file = _write(env_dir, "ref2.env", "VALID=\n")
    env = parse_env_file(source_file)
    ref = parse_env_file(ref_file)
    result = strip_keys(env, ref)
    assert result.removed_count == 1
    assert result.removed[0].key == "ORPHAN"
    # comments are never parsed as keys
    assert all(r.key != "# this is a comment" for r in result.removed)


def test_as_dict_round_trip(env_dir):
    source_file = _write(env_dir, "src.env", "X=10\nY=20\nZ=30\n")
    ref_file = _write(env_dir, "tmpl.env", "X=\nY=\n")
    env = parse_env_file(source_file)
    ref = parse_env_file(ref_file)
    result = strip_keys(env, ref, source="src.env", reference_name="tmpl.env")
    d = result.as_dict()
    assert d["removed_count"] == 1
    assert d["kept"] == {"X": "10", "Y": "20"}
    assert d["removed"][0]["key"] == "Z"
