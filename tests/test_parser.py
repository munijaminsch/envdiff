"""Tests for envdiff.parser module."""

import pytest
from pathlib import Path

from envdiff.parser import parse_env_file, EnvParseError


@pytest.fixture
def tmp_env(tmp_path):
    """Helper that writes content to a temp .env file and returns its path."""
    def _write(content: str) -> Path:
        env_file = tmp_path / ".env"
        env_file.write_text(content, encoding="utf-8")
        return env_file
    return _write


def test_basic_key_value(tmp_env):
    path = tmp_env("KEY=value\nANOTHER=123\n")
    result = parse_env_file(path)
    assert result == {"KEY": "value", "ANOTHER": "123"}


def test_ignores_comments_and_blank_lines(tmp_env):
    content = "# This is a comment\n\nKEY=hello\n\n# another comment\n"
    result = parse_env_file(tmp_env(content))
    assert result == {"KEY": "hello"}


def test_strips_double_quotes(tmp_env):
    result = parse_env_file(tmp_env('DB_URL="postgres://localhost/db"\n'))
    assert result["DB_URL"] == "postgres://localhost/db"


def test_strips_single_quotes(tmp_env):
    result = parse_env_file(tmp_env("SECRET='my secret value'\n"))
    assert result["SECRET"] == "my secret value"


def test_export_prefix(tmp_env):
    result = parse_env_file(tmp_env("export PORT=8080\n"))
    assert result["PORT"] == "8080"


def test_empty_value(tmp_env):
    result = parse_env_file(tmp_env("EMPTY=\n"))
    assert result["EMPTY"] == ""


def test_value_with_equals_sign(tmp_env):
    result = parse_env_file(tmp_env("TOKEN=abc=def==\n"))
    assert result["TOKEN"] == "abc=def=="


def test_file_not_found():
    with pytest.raises(FileNotFoundError):
        parse_env_file("/nonexistent/path/.env")


def test_invalid_line_raises_parse_error(tmp_env):
    with pytest.raises(EnvParseError, match="Invalid syntax"):
        parse_env_file(tmp_env("INVALID_LINE_NO_EQUALS\n"))


def test_empty_key_raises_parse_error(tmp_env):
    with pytest.raises(EnvParseError, match="Empty key"):
        parse_env_file(tmp_env("=value\n"))


def test_returns_dict_type(tmp_env):
    result = parse_env_file(tmp_env("A=1\n"))
    assert isinstance(result, dict)


def test_inline_comment_stripped(tmp_env):
    """Values should have inline comments stripped when unquoted."""
    result = parse_env_file(tmp_env("HOST=localhost # the host\n"))
    assert result["HOST"] == "localhost"


def test_inline_comment_preserved_in_quoted_value(tmp_env):
    """Inline comments inside quoted values should be preserved as part of the value."""
    result = parse_env_file(tmp_env('MSG="hello # world"\n'))
    assert result["MSG"] == "hello # world"
