"""Integration tests: parse real .env files then generate a template."""
from pathlib import Path

import pytest

from envdiff.parser import parse_env_file
from envdiff.templater import build_template, write_template


@pytest.fixture()
def env_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(directory: Path, name: str, content: str) -> Path:
    p = directory / name
    p.write_text(content, encoding="utf-8")
    return p


def test_template_from_two_env_files(env_dir: Path):
    _write(env_dir, ".env.dev", "DB_HOST=localhost\nDB_PORT=5432\nDEBUG=true\n")
    _write(env_dir, ".env.prod", "DB_HOST=prod.db\nDB_PORT=5432\nSECRET_KEY=abc\n")

    dev = parse_env_file(env_dir / ".env.dev")
    prod = parse_env_file(env_dir / ".env.prod")

    result = build_template([dev, prod])

    assert set(result.keys) == {"DB_HOST", "DB_PORT", "DEBUG", "SECRET_KEY"}
    # Values must be redacted
    assert "localhost" not in result.content
    assert "abc" not in result.content
    assert "CHANGE_ME" in result.content


def test_template_placeholder_not_original_value(env_dir: Path):
    _write(env_dir, ".env", "API_KEY=super_secret\nREGION=us-east-1\n")
    parsed = parse_env_file(env_dir / ".env")
    result = build_template([parsed], placeholder="<fill-in>")

    for line in result.content.splitlines():
        if line and not line.startswith("#"):
            assert line.endswith("=<fill-in>"), f"unexpected line: {line!r}"


def test_write_then_parse_template(env_dir: Path):
    """A written template should itself be parseable by parse_env_file."""
    _write(env_dir, ".env", "FOO=bar\nBAZ=qux\n")
    parsed = parse_env_file(env_dir / ".env")

    result = build_template([parsed], placeholder="PLACEHOLDER")
    out = env_dir / ".env.template"
    write_template(result, out)

    re_parsed = parse_env_file(out)
    assert set(re_parsed.keys()) == {"FOO", "BAZ"}
    assert all(v == "PLACEHOLDER" for v in re_parsed.values())


def test_template_with_header_comment(env_dir: Path):
    _write(env_dir, ".env", "PORT=8080\n")
    parsed = parse_env_file(env_dir / ".env")
    result = build_template([parsed], comment_header="Copy this file to .env and fill in values")
    lines = result.content.splitlines()
    assert lines[0].startswith("#")
    assert "Copy this file" in lines[0]
