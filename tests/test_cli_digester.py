"""Tests for envdiff.cli_digester."""
import pathlib
import json
import pytest

from envdiff.cli_digester import run_digest


@pytest.fixture()
def env_dir(tmp_path: pathlib.Path):
    return tmp_path


def _write(directory: pathlib.Path, name: str, content: str) -> pathlib.Path:
    p = directory / name
    p.write_text(content)
    return p


class _Args:
    def __init__(self, files, algorithm="sha256", use_json=False):
        self.files = files
        self.algorithm = algorithm
        self.use_json = use_json


def test_single_file_exits_zero(env_dir, capsys):
    p = _write(env_dir, "a.env", "KEY=val\n")
    code = run_digest(_Args([str(p)]))
    assert code == 0


def test_single_file_prints_digest(env_dir, capsys):
    p = _write(env_dir, "a.env", "KEY=val\n")
    run_digest(_Args([str(p)]))
    out = capsys.readouterr().out
    assert "digest" in out
    assert "keys" in out


def test_two_identical_files_no_diff(env_dir, capsys):
    content = "KEY=val\nOTHER=x\n"
    p1 = _write(env_dir, "a.env", content)
    p2 = _write(env_dir, "b.env", content)
    code = run_digest(_Args([str(p1), str(p2)]))
    assert code == 0
    out = capsys.readouterr().out
    assert "no differences" in out.lower()


def test_two_different_files_shows_changed(env_dir, capsys):
    p1 = _write(env_dir, "a.env", "KEY=old\n")
    p2 = _write(env_dir, "b.env", "KEY=new\n")
    run_digest(_Args([str(p1), str(p2)]))
    out = capsys.readouterr().out
    assert "KEY" in out
    assert "changed" in out


def test_json_output_single_file(env_dir, capsys):
    p = _write(env_dir, "a.env", "K=v\n")
    code = run_digest(_Args([str(p)], use_json=True))
    assert code == 0
    data = json.loads(capsys.readouterr().out)
    assert "hex_digest" in data
    assert "key_count" in data


def test_json_output_two_files(env_dir, capsys):
    p1 = _write(env_dir, "a.env", "K=v\n")
    p2 = _write(env_dir, "b.env", "K=v\n")
    run_digest(_Args([str(p1), str(p2)], use_json=True))
    data = json.loads(capsys.readouterr().out)
    assert "left" in data
    assert "right" in data
    assert "diffs" in data


def test_more_than_two_files_returns_error(env_dir):
    p = _write(env_dir, "a.env", "K=v\n")
    code = run_digest(_Args([str(p), str(p), str(p)]))
    assert code == 2


def test_missing_file_returns_error(env_dir):
    code = run_digest(_Args(["/nonexistent/path.env"]))
    assert code == 1


def test_md5_algorithm_accepted(env_dir, capsys):
    p = _write(env_dir, "a.env", "K=v\n")
    code = run_digest(_Args([str(p)], algorithm="md5"))
    assert code == 0
    out = capsys.readouterr().out
    assert "md5" in out
