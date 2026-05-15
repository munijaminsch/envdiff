"""Tests for envdiff.differ — high-level diff orchestration."""

import pytest

from pathlib import Path
from envdiff.differ import DiffError, DiffOptions, diff_files


@pytest.fixture()
def env_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(directory: Path, name: str, content: str) -> Path:
    p = directory / name
    p.write_text(content)
    return p


def test_diff_files_no_differences(env_dir):
    left = _write(env_dir, ".env.left", "KEY=value\nFOO=bar\n")
    right = _write(env_dir, ".env.right", "KEY=value\nFOO=bar\n")
    result = diff_files(left, right)
    assert not result.has_differences()


def test_diff_files_detects_missing_in_right(env_dir):
    left = _write(env_dir, ".env.left", "KEY=value\nEXTRA=only_left\n")
    right = _write(env_dir, ".env.right", "KEY=value\n")
    result = diff_files(left, right)
    missing = [d.key for d in result.missing_in_right()]
    assert "EXTRA" in missing


def test_diff_files_detects_missing_in_left(env_dir):
    left = _write(env_dir, ".env.left", "KEY=value\n")
    right = _write(env_dir, ".env.right", "KEY=value\nNEW=only_right\n")
    result = diff_files(left, right)
    missing = [d.key for d in result.missing_in_left()]
    assert "NEW" in missing


def test_diff_files_detects_value_mismatch(env_dir):
    left = _write(env_dir, ".env.left", "KEY=alpha\n")
    right = _write(env_dir, ".env.right", "KEY=beta\n")
    result = diff_files(left, right)
    mismatched = [d.key for d in result.mismatched()]
    assert "KEY" in mismatched


def test_diff_files_stores_file_names(env_dir):
    left = _write(env_dir, ".env.dev", "A=1\n")
    right = _write(env_dir, ".env.prod", "A=1\n")
    result = diff_files(left, right)
    assert result.left_name == ".env.dev"
    assert result.right_name == ".env.prod"


def test_diff_files_with_include_pattern(env_dir):
    left = _write(env_dir, ".env.left", "DB_HOST=localhost\nAPP_NAME=myapp\n")
    right = _write(env_dir, ".env.right", "DB_HOST=remotehost\n")
    opts = DiffOptions(include_patterns=["DB_*"])
    result = diff_files(left, right, options=opts)
    all_keys = {d.key for d in result.diffs}
    assert "APP_NAME" not in all_keys
    assert "DB_HOST" in all_keys


def test_diff_files_with_exclude_pattern(env_dir):
    left = _write(env_dir, ".env.left", "SECRET_KEY=abc\nPORT=8080\n")
    right = _write(env_dir, ".env.right", "PORT=9090\n")
    opts = DiffOptions(exclude_patterns=["SECRET_*"])
    result = diff_files(left, right, options=opts)
    all_keys = {d.key for d in result.diffs}
    assert "SECRET_KEY" not in all_keys


def test_diff_files_with_prefix_filter(env_dir):
    left = _write(env_dir, ".env.left", "DB_HOST=localhost\nAPP_ENV=dev\n")
    right = _write(env_dir, ".env.right", "DB_HOST=localhost\n")
    opts = DiffOptions(prefix="DB_")
    result = diff_files(left, right, options=opts)
    all_keys = {d.key for d in result.diffs}
    assert "APP_ENV" not in all_keys


def test_diff_files_raises_diff_error_on_bad_file(env_dir):
    missing = env_dir / "nonexistent.env"
    right = _write(env_dir, ".env.right", "KEY=value\n")
    with pytest.raises(DiffError):
        diff_files(missing, right)
