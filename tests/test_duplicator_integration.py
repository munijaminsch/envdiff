"""Integration tests: parse a real .env file then run duplicate detection."""

import pathlib
import textwrap

import pytest

from envdiff.parser import parse_env_file
from envdiff.duplicator import find_duplicates


@pytest.fixture()
def env_dir(tmp_path: pathlib.Path) -> pathlib.Path:
    return tmp_path


def _write(directory: pathlib.Path, name: str, content: str) -> pathlib.Path:
    p = directory / name
    p.write_text(textwrap.dedent(content))
    return p


def test_clean_file_has_no_duplicates(env_dir):
    p = _write(env_dir, ".env", """
        DB_HOST=localhost
        DB_PORT=5432
        APP_SECRET=hunter2
    """)
    env = parse_env_file(str(p))
    result = find_duplicates(env, source=str(p))
    assert result.is_clean


def test_duplicate_values_detected_after_parse(env_dir):
    p = _write(env_dir, ".env", """
        TOKEN=abc123
        API_KEY=abc123
        OTHER=different
    """)
    env = parse_env_file(str(p))
    result = find_duplicates(env, source=str(p))
    assert not result.is_clean
    assert len(result.groups) == 1
    assert set(result.groups[0].keys) == {"TOKEN", "API_KEY"}


def test_ignore_empty_integration(env_dir):
    p = _write(env_dir, ".env", """
        OPTIONAL_A=
        OPTIONAL_B=
        REAL_KEY=value
    """)
    env = parse_env_file(str(p))

    with_empty = find_duplicates(env, ignore_empty=False)
    without_empty = find_duplicates(env, ignore_empty=True)

    assert not with_empty.is_clean          # empty strings are duplicates
    assert without_empty.is_clean           # empty strings ignored


def test_as_dict_round_trip(env_dir):
    p = _write(env_dir, ".env", """
        X=same
        Y=same
    """)
    env = parse_env_file(str(p))
    result = find_duplicates(env, source=".env")
    d = result.as_dict()
    assert isinstance(d, dict)
    assert d["source"] == ".env"
    assert len(d["duplicate_groups"]) == 1
