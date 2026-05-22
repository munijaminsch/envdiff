"""Integration tests for envdiff.linker using real parsed files."""
import pytest
from pathlib import Path
from envdiff.parser import parse_env_file
from envdiff.linker import link_envs


@pytest.fixture()
def env_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(path: Path, content: str) -> Path:
    path.write_text(content)
    return path


def test_link_two_identical_parsed_files(env_dir):
    a = _write(env_dir / "a.env", "HOST=localhost\nPORT=5432\n")
    b = _write(env_dir / "b.env", "HOST=localhost\nPORT=5432\n")
    left = parse_env_file(str(a))
    right = parse_env_file(str(b))
    result = link_envs(left, right, left_source=str(a), right_source=str(b))
    assert result.is_clean is True
    assert set(result.shared_keys) == {"HOST", "PORT"}
    assert result.exclusive_left == []
    assert result.exclusive_right == []


def test_link_detects_drift_after_parse(env_dir):
    a = _write(env_dir / "a.env", "HOST=localhost\nPORT=5432\n")
    b = _write(env_dir / "b.env", "HOST=remotehost\nPORT=5432\n")
    left = parse_env_file(str(a))
    right = parse_env_file(str(b))
    result = link_envs(left, right)
    assert result.is_clean is False
    mismatched = [e for e in result.entries if not e.values_match and e.is_shared]
    assert any(e.key == "HOST" for e in mismatched)


def test_comments_not_included_after_parse(env_dir):
    a = _write(env_dir / "a.env", "# comment\nKEY=val\n")
    b = _write(env_dir / "b.env", "KEY=val\n")
    left = parse_env_file(str(a))
    right = parse_env_file(str(b))
    result = link_envs(left, right)
    keys = [e.key for e in result.entries]
    assert "# comment" not in keys
    assert "KEY" in keys


def test_exclusive_keys_surface_correctly(env_dir):
    a = _write(env_dir / "a.env", "SHARED=1\nLEFT_ONLY=x\n")
    b = _write(env_dir / "b.env", "SHARED=1\nRIGHT_ONLY=y\n")
    left = parse_env_file(str(a))
    right = parse_env_file(str(b))
    result = link_envs(left, right, left_source="a", right_source="b")
    assert "LEFT_ONLY" in result.exclusive_left
    assert "RIGHT_ONLY" in result.exclusive_right
    assert result.total_keys == 3
