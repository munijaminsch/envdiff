"""Integration tests: parse a real .env file then prune it."""

import pathlib
import pytest

from envdiff.parser import parse_env_file
from envdiff.pruner import prune


@pytest.fixture()
def env_dir(tmp_path: pathlib.Path) -> pathlib.Path:
    return tmp_path


def _write(directory: pathlib.Path, name: str, content: str) -> pathlib.Path:
    p = directory / name
    p.write_text(content)
    return p


def test_prune_parsed_file_keeps_allowed():
    import tempfile, pathlib
    with tempfile.TemporaryDirectory() as td:
        p = pathlib.Path(td) / ".env"
        p.write_text("APP_HOST=localhost\nAPP_PORT=8080\nSECRET_KEY=abc\nDB_URL=postgres\n")
        env = parse_env_file(str(p))
        result = prune(env, allowed_patterns=[r"^APP_"], source=str(p))
    assert result.kept_count == 2
    assert result.removed_count == 2


def test_clean_file_no_removals():
    import tempfile, pathlib
    with tempfile.TemporaryDirectory() as td:
        p = pathlib.Path(td) / ".env"
        p.write_text("A=1\nB=2\n")
        env = parse_env_file(str(p))
        result = prune(env, allowed_keys=list(env.keys()), source=str(p))
    assert result.is_clean


def test_comments_not_included_after_parse():
    import tempfile, pathlib
    with tempfile.TemporaryDirectory() as td:
        p = pathlib.Path(td) / ".env"
        p.write_text("# comment\nA=1\n\nB=2\n")
        env = parse_env_file(str(p))
        result = prune(env, allowed_keys=["A", "B"])
    # comments/blanks are not keys — nothing should be removed
    assert result.removed_count == 0


def test_as_dict_round_trip():
    import tempfile, pathlib
    with tempfile.TemporaryDirectory() as td:
        p = pathlib.Path(td) / ".env"
        p.write_text("X=10\nY=20\nZ=30\n")
        env = parse_env_file(str(p))
        result = prune(env, allowed_keys=["X", "Z"])
    d = result.as_dict()
    keys_in_dict = {e["key"] for e in d["entries"]}
    assert keys_in_dict == {"X", "Y", "Z"}
    removed = [e for e in d["entries"] if e["removed"]]
    assert len(removed) == 1
    assert removed[0]["key"] == "Y"
