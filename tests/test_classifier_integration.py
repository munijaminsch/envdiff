"""Integration tests for classifier using real .env files."""

import pathlib
import pytest

from envdiff.parser import parse_env_file
from envdiff.classifier import classify_env


@pytest.fixture()
def env_dir(tmp_path: pathlib.Path) -> pathlib.Path:
    return tmp_path


def _write(directory: pathlib.Path, name: str, content: str) -> pathlib.Path:
    p = directory / name
    p.write_text(content)
    return p


def test_classify_parsed_file(env_dir):
    p = _write(
        env_dir,
        "app.env",
        "PORT=8080\nDEBUG=true\nDATABASE_URL=postgres://localhost/db\nAPP_NAME=myapp\n",
    )
    env = parse_env_file(str(p))
    result = classify_env(env, source=str(p))
    assert result.total_keys == 4
    types = {c.key: c.inferred_type for c in result.classifications}
    assert types["PORT"] == "integer"
    assert types["DEBUG"] == "boolean"
    assert types["APP_NAME"] == "string"


def test_empty_values_detected_after_parse(env_dir):
    p = _write(env_dir, "partial.env", "PRESENT=hello\nMISSING=\n")
    env = parse_env_file(str(p))
    result = classify_env(env, source="partial.env")
    groups = result.by_type()
    assert "empty" in groups
    assert groups["empty"][0].key == "MISSING"


def test_as_dict_round_trip(env_dir):
    p = _write(env_dir, "simple.env", "TIMEOUT=30\nENABLED=yes\n")
    env = parse_env_file(str(p))
    result = classify_env(env, source="simple.env")
    d = result.as_dict()
    assert d["total_keys"] == 2
    keys_in_dict = [item["key"] for item in d["classifications"]]
    assert "TIMEOUT" in keys_in_dict
    assert "ENABLED" in keys_in_dict
