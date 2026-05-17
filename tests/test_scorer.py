"""Tests for envdiff.scorer."""

import pytest

from envdiff.comparator import CompareResult, KeyDiff
from envdiff.scorer import ScoreError, SimilarityScore, score_result


def _make_result(
    matches=None,
    missing_in_right=None,
    missing_in_left=None,
    mismatches=None,
    left_file="left.env",
    right_file="right.env",
) -> CompareResult:
    return CompareResult(
        left_file=left_file,
        right_file=right_file,
        matches=matches or {},
        missing_in_right=missing_in_right or {},
        missing_in_left=missing_in_left or {},
        mismatches=mismatches or {},
    )


def test_score_result_returns_similarity_score():
    result = _make_result(matches={"A": "1"})
    score = score_result(result)
    assert isinstance(score, SimilarityScore)


def test_score_preserves_file_names():
    result = _make_result(left_file="a.env", right_file="b.env")
    score = score_result(result)
    assert score.left_file == "a.env"
    assert score.right_file == "b.env"


def test_perfect_match_overall_is_one():
    result = _make_result(matches={"A": "1", "B": "2"})
    score = score_result(result)
    assert score.overall == 1.0
    assert score.key_overlap == 1.0
    assert score.value_similarity == 1.0


def test_empty_result_overall_is_one():
    result = _make_result()
    score = score_result(result)
    assert score.overall == 1.0


def test_missing_in_right_lowers_key_overlap():
    result = _make_result(
        matches={"A": "1"},
        missing_in_right={"B": "2"},
    )
    score = score_result(result)
    # 2 total keys, 1 missing in right → overlap = 1/2
    assert score.key_overlap == 0.5


def test_mismatch_lowers_value_similarity():
    result = _make_result(
        matches={"A": "1"},
        mismatches={"B": KeyDiff(key="B", left_value="x", right_value="y")},
    )
    score = score_result(result)
    # 2 shared keys, 1 matching → value_similarity = 0.5
    assert score.value_similarity == 0.5


def test_overall_is_product_of_overlap_and_similarity():
    result = _make_result(
        matches={"A": "1"},
        missing_in_right={"B": "2"},
        mismatches={"C": KeyDiff(key="C", left_value="x", right_value="y")},
    )
    score = score_result(result)
    assert score.overall == round(score.key_overlap * score.value_similarity, 4)


def test_as_dict_contains_expected_keys():
    result = _make_result(matches={"X": "1"})
    d = score_result(result).as_dict()
    for key in (
        "left_file", "right_file", "total_keys", "matching_keys",
        "missing_in_right", "missing_in_left", "mismatched_values",
        "key_overlap", "value_similarity", "overall",
    ):
        assert key in d


def test_score_error_on_invalid_input():
    with pytest.raises(ScoreError):
        score_result({"not": "a CompareResult"})
