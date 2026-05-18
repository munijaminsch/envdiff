"""Integration tests for inspector: parse a real file then inspect it."""

from pathlib import Path
import pytest

from envdiff.parser import parse_env_file
from envdiff.inspector import inspect_env, InspectResult


@pytest.fixture()
def env_dir(tmp_path: Path):
    return tmp_path


def _write(directory: Path, name: str, content: str) -> Path:
    p = directory / name
    p.write_text(content)
    return p


def test_parse_then_inspect_counts_keys(env_dir):
    p = _write(env_dir, ".env", "A=1\nB=2\nC=3\n")
    env = parse_env_file(p)
    result = inspect_env(env, source=str(p))
    assert result.total_keys == 3


def test_parse_then_inspect_detects_empty(env_dir):
    p = _write(env_dir, ".env", "PRESENT=hello\nMISSING=\n")
    env = parse_env_file(p)
    result = inspect_env(env, source=str(p))
    assert "MISSING" in result.empty_keys
    assert "PRESENT" not in result.empty_keys


def test_parse_ignores_comments_inspector_sees_real_keys(env_dir):
    content = "# comment\nKEY=value\n\nOTHER=123\n"
    p = _write(env_dir, ".env", content)
    env = parse_env_file(p)
    result = inspect_env(env, source=str(p))
    assert result.total_keys == 2
    assert "OTHER" in result.numeric_keys


def test_as_dict_round_trip(env_dir):
    p = _write(env_dir, ".env", "DEBUG=false\nPORT=8000\n")
    env = parse_env_file(p)
    result = inspect_env(env, source=str(p))
    d = result.as_dict()
    assert d["source"] == str(p)
    assert any(i["key"] == "DEBUG" for i in d["inspections"])
    assert any(i["is_boolean"] for i in d["inspections"])
    assert any(i["is_numeric"] for i in d["inspections"])
