"""Tests for envdiff.templater."""
from pathlib import Path

import pytest

from envdiff.templater import (
    TemplateError,
    TemplateResult,
    build_template,
    write_template,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _env(**kwargs: str) -> dict:
    return dict(kwargs)


# ---------------------------------------------------------------------------
# build_template
# ---------------------------------------------------------------------------

def test_returns_template_result():
    result = build_template([_env(FOO="1", BAR="2")])
    assert isinstance(result, TemplateResult)


def test_keys_sorted_by_default():
    result = build_template([_env(ZEBRA="z", ALPHA="a", MIDDLE="m")])
    assert result.keys == ["ALPHA", "MIDDLE", "ZEBRA"]


def test_keys_unsorted_when_flag_false():
    env = {"ZEBRA": "z", "ALPHA": "a"}
    result = build_template([env], sort_keys=False)
    assert result.keys == ["ZEBRA", "ALPHA"]


def test_content_contains_placeholder():
    result = build_template([_env(SECRET="real_value")], placeholder="CHANGE_ME")
    assert "SECRET=CHANGE_ME" in result.content


def test_custom_placeholder():
    result = build_template([_env(API_KEY="abc")], placeholder="<required>")
    assert "API_KEY=<required>" in result.content


def test_empty_placeholder_raises():
    with pytest.raises(TemplateError, match="placeholder must not be empty"):
        build_template([_env(FOO="1")], placeholder="")


def test_merges_keys_from_multiple_envs():
    result = build_template([_env(A="1"), _env(B="2"), _env(A="x", C="3")])
    assert set(result.keys) == {"A", "B", "C"}


def test_key_count_property():
    result = build_template([_env(X="1", Y="2", Z="3")])
    assert result.key_count == 3


def test_comment_header_prepended():
    result = build_template([_env(FOO="1")], comment_header="Auto-generated template")
    assert result.content.startswith("# Auto-generated template")


def test_comment_header_already_prefixed():
    result = build_template([_env(FOO="1")], comment_header="# My header")
    assert "# My header" in result.content
    assert "## My header" not in result.content


def test_content_ends_with_newline():
    result = build_template([_env(FOO="1")])
    assert result.content.endswith("\n")


def test_empty_envs_produces_empty_content():
    result = build_template([])
    assert result.key_count == 0
    assert result.content == ""


def test_non_dict_raises():
    with pytest.raises(TemplateError, match="expected dict"):
        build_template([["FOO=bar"]])  # type: ignore[list-item]


def test_as_dict_structure():
    result = build_template([_env(FOO="1")], placeholder="X")
    d = result.as_dict()
    assert d["key_count"] == 1
    assert d["placeholder"] == "X"
    assert "FOO" in d["keys"]


# ---------------------------------------------------------------------------
# write_template
# ---------------------------------------------------------------------------

def test_write_template_creates_file(tmp_path: Path):
    result = build_template([_env(FOO="1")])
    out = tmp_path / "out" / ".env.template"
    write_template(result, out)
    assert out.exists()


def test_write_template_content_matches(tmp_path: Path):
    result = build_template([_env(FOO="1", BAR="2")])
    out = tmp_path / ".env.template"
    write_template(result, out)
    assert out.read_text(encoding="utf-8") == result.content
