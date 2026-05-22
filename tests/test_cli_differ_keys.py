import json
import os
import pytest
from envdiff.cli_differ_keys import run_keys


@pytest.fixture
def env_dir(tmp_path):
    return tmp_path


def _write(path, content):
    path.write_text(content)
    return str(path)


class _Args:
    def __init__(self, left, right, fmt="text", fail=False):
        self.left = left
        self.right = right
        self.fmt = fmt
        self.fail = fail


def test_clean_files_exits_zero(env_dir):
    left = _write(env_dir / ".env.left", "A=1\nB=2\n")
    right = _write(env_dir / ".env.right", "A=1\nB=2\n")
    assert run_keys(_Args(left, right)) == 0


def test_exclusive_keys_exits_zero_without_flag(env_dir):
    left = _write(env_dir / ".env.left", "A=1\nB=2\n")
    right = _write(env_dir / ".env.right", "A=1\n")
    assert run_keys(_Args(left, right, fail=False)) == 0


def test_exclusive_keys_exits_one_with_flag(env_dir):
    left = _write(env_dir / ".env.left", "A=1\nB=2\n")
    right = _write(env_dir / ".env.right", "A=1\n")
    assert run_keys(_Args(left, right, fail=True)) == 1


def test_missing_left_file_exits_one(env_dir):
    right = _write(env_dir / ".env.right", "A=1\n")
    args = _Args(str(env_dir / "missing.env"), right)
    assert run_keys(args) == 1


def test_json_output_is_valid(env_dir, capsys):
    left = _write(env_dir / ".env.left", "A=1\nB=2\n")
    right = _write(env_dir / ".env.right", "A=1\n")
    run_keys(_Args(left, right, fmt="json"))
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "only_in_left" in data
    assert "only_in_right" in data


def test_text_output_clean_message(env_dir, capsys):
    left = _write(env_dir / ".env.left", "A=1\n")
    right = _write(env_dir / ".env.right", "A=1\n")
    run_keys(_Args(left, right, fmt="text"))
    captured = capsys.readouterr()
    assert "No exclusive keys" in captured.out


def test_text_output_shows_exclusive_key(env_dir, capsys):
    left = _write(env_dir / ".env.left", "A=1\nSECRET=xyz\n")
    right = _write(env_dir / ".env.right", "A=1\n")
    run_keys(_Args(left, right, fmt="text"))
    captured = capsys.readouterr()
    assert "SECRET" in captured.out
