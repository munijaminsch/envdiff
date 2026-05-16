"""Tests for envdiff.profiler."""

from pathlib import Path

import pytest

from envdiff.profiler import EnvProfile, ProfileError, profile_env_file


@pytest.fixture()
def tmp_env(tmp_path: Path):
    def _write(name: str, content: str) -> Path:
        p = tmp_path / name
        p.write_text(content)
        return p

    return _write


def test_profile_returns_env_profile(tmp_env):
    p = tmp_env(".env", "KEY=value\nOTHER=thing\n")
    result = profile_env_file(p)
    assert isinstance(result, EnvProfile)


def test_total_keys_count(tmp_env):
    p = tmp_env(".env", "A=1\nB=2\nC=3\n")
    result = profile_env_file(p)
    assert result.total_keys == 3


def test_detects_empty_values(tmp_env):
    p = tmp_env(".env", "FULL=value\nEMPTY=\nALSO_EMPTY=\n")
    result = profile_env_file(p)
    assert set(result.empty_values) == {"EMPTY", "ALSO_EMPTY"}
    assert result.empty_count == 2


def test_no_empty_values(tmp_env):
    p = tmp_env(".env", "A=hello\nB=world\n")
    result = profile_env_file(p)
    assert result.empty_values == []
    assert result.empty_count == 0


def test_detects_duplicate_values(tmp_env):
    p = tmp_env(".env", "X=same\nY=same\nZ=different\n")
    result = profile_env_file(p)
    assert result.duplicate_value_groups == 1
    assert set(result.duplicate_values["same"]) == {"X", "Y"}


def test_no_duplicate_values(tmp_env):
    p = tmp_env(".env", "A=one\nB=two\nC=three\n")
    result = profile_env_file(p)
    assert result.duplicate_value_groups == 0
    assert result.duplicate_values == {}


def test_longest_key(tmp_env):
    p = tmp_env(".env", "SHORT=a\nMUCH_LONGER_KEY=b\nMED=c\n")
    result = profile_env_file(p)
    assert result.longest_key == "MUCH_LONGER_KEY"


def test_longest_value_key(tmp_env):
    p = tmp_env(".env", "A=hi\nB=a_very_long_value_here\nC=mid\n")
    result = profile_env_file(p)
    assert result.longest_value_key == "B"


def test_as_dict_contains_expected_keys(tmp_env):
    p = tmp_env(".env", "K=v\n")
    result = profile_env_file(p).as_dict()
    expected = {
        "path", "total_keys", "empty_count", "empty_values",
        "duplicate_value_groups", "duplicate_values",
        "longest_key", "longest_value_key",
    }
    assert set(result.keys()) == expected


def test_raises_profile_error_for_missing_file():
    with pytest.raises(ProfileError, match="File not found"):
        profile_env_file("/nonexistent/path/.env")


def test_path_stored_in_profile(tmp_env):
    p = tmp_env(".env", "A=1\n")
    result = profile_env_file(p)
    assert result.path == str(p)
