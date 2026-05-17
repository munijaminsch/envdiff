"""Integration tests: parse a real .env file then annotate it."""
import pathlib
import pytest

from envdiff.parser import parse_env_file
from envdiff.annotator import annotate, AnnotationResult


@pytest.fixture()
def env_dir(tmp_path: pathlib.Path) -> pathlib.Path:
    return tmp_path


def _write(path: pathlib.Path, content: str) -> pathlib.Path:
    path.write_text(content)
    return path


def test_annotate_parsed_file(env_dir):
    f = _write(
        env_dir / ".env",
        "APP_NAME=myapp\nDB_PASSWORD=s3cr3t\nPORT=5432\nDEBUG=false\nEMPTY=\n",
    )
    env = parse_env_file(str(f))
    result = annotate(env, source=str(f))

    assert isinstance(result, AnnotationResult)
    assert result.total_keys == 5
    assert "EMPTY" in result.empty_keys
    assert "sensitive" in result.annotations["DB_PASSWORD"].tags
    assert "numeric" in result.annotations["PORT"].tags
    assert "boolean" in result.annotations["DEBUG"].tags


def test_annotate_url_value(env_dir):
    f = _write(env_dir / ".env", "API_URL=https://api.example.com\n")
    env = parse_env_file(str(f))
    result = annotate(env, source="prod")
    assert "url" in result.annotations["API_URL"].tags


def test_as_dict_round_trip(env_dir):
    f = _write(env_dir / ".env", "FOO=bar\nBAZ=\n")
    env = parse_env_file(str(f))
    result = annotate(env, source="staging")
    d = result.as_dict()

    assert d["source"] == "staging"
    assert d["total_keys"] == 2
    assert d["annotations"]["BAZ"]["is_empty"] is True
    assert d["annotations"]["FOO"]["is_empty"] is False
