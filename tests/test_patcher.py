"""Tests for envdiff.patcher."""
from pathlib import Path

import pytest

from envdiff.patcher import PatchError, PatchResult, patch_env, patch_env_file


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

SAMPLE = """# database config
DB_HOST=localhost
DB_PORT=5432
DB_NAME=mydb

SECRET_KEY=old_secret
"""


# ---------------------------------------------------------------------------
# patch_env (string-level)
# ---------------------------------------------------------------------------

def test_returns_patch_result():
    result = patch_env(SAMPLE, {})
    assert isinstance(result, PatchResult)


def test_no_patches_leaves_content_unchanged():
    result = patch_env(SAMPLE, {})
    assert result.content == SAMPLE
    assert result.changed_count == 0
    assert result.added_count == 0


def test_updates_existing_key():
    result = patch_env(SAMPLE, {"DB_HOST": "prod-db.example.com"})
    assert "DB_HOST=prod-db.example.com" in result.content
    assert result.changed_count == 1
    assert "DB_HOST" in result.updated


def test_updates_multiple_keys():
    result = patch_env(SAMPLE, {"DB_HOST": "newhost", "DB_PORT": "3306"})
    assert result.changed_count == 2
    assert "DB_HOST=newhost" in result.content
    assert "DB_PORT=3306" in result.content


def test_original_value_replaced_not_duplicated():
    result = patch_env(SAMPLE, {"SECRET_KEY": "new_secret"})
    assert result.content.count("SECRET_KEY=") == 1
    assert "SECRET_KEY=new_secret" in result.content
    assert "old_secret" not in result.content


def test_adds_missing_key_by_default():
    result = patch_env(SAMPLE, {"NEW_KEY": "hello"})
    assert result.added_count == 1
    assert "NEW_KEY=hello" in result.content
    assert "NEW_KEY" in result.added


def test_does_not_add_missing_key_when_flag_false():
    result = patch_env(SAMPLE, {"NEW_KEY": "hello"}, add_missing=False)
    assert result.added_count == 0
    assert "NEW_KEY" not in result.content


def test_comments_preserved():
    result = patch_env(SAMPLE, {"DB_PORT": "9999"})
    assert "# database config" in result.content


def test_invalid_patches_type_raises():
    with pytest.raises(PatchError):
        patch_env(SAMPLE, "not-a-dict")  # type: ignore


def test_as_dict_structure():
    result = patch_env(SAMPLE, {"DB_HOST": "x", "NEW": "y"})
    d = result.as_dict()
    assert "source" in d
    assert "changed_count" in d
    assert "added_count" in d
    assert "updated" in d
    assert "added" in d


# ---------------------------------------------------------------------------
# patch_env_file (file-level)
# ---------------------------------------------------------------------------

@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text(SAMPLE, encoding="utf-8")
    return p


def test_patch_env_file_returns_result(env_file: Path):
    result = patch_env_file(env_file, {"DB_NAME": "proddb"})
    assert isinstance(result, PatchResult)
    assert result.source == str(env_file)


def test_patch_env_file_write_updates_file(env_file: Path):
    patch_env_file(env_file, {"DB_NAME": "proddb"}, write=True)
    assert "DB_NAME=proddb" in env_file.read_text(encoding="utf-8")


def test_patch_env_file_no_write_leaves_file(env_file: Path):
    patch_env_file(env_file, {"DB_NAME": "proddb"}, write=False)
    assert "DB_NAME=mydb" in env_file.read_text(encoding="utf-8")


def test_patch_env_file_missing_path_raises(tmp_path: Path):
    with pytest.raises(PatchError, match="File not found"):
        patch_env_file(tmp_path / "ghost.env", {})
