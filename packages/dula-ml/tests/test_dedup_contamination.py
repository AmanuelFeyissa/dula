"""Unit tests for dedup and contamination controls."""

from __future__ import annotations

import pytest
from dula_ml.contamination import ContaminationError, assert_no_contamination, eval_hashes
from dula_ml.dedup import content_hash, dedup, normalize
from dula_ml.records import SFTRecord


def _rec(instruction: str, output: str = "answer") -> SFTRecord:
    return SFTRecord(instruction=instruction, output=output)


def test_normalize_and_hash_are_whitespace_case_insensitive() -> None:
    assert content_hash("Brute  Force") == content_hash("brute force")
    assert normalize("  A  B ") == "a b"


def test_dedup_removes_exact_duplicates_preserving_order() -> None:
    records = [_rec("a"), _rec("b"), _rec("a"), _rec("c")]
    unique, removed = dedup(records)
    assert [r.instruction for r in unique] == ["a", "b", "c"]
    assert removed == 1


def test_contamination_detected_and_raises() -> None:
    evalset = eval_hashes(["What is Log4Shell?"])
    clean = [_rec("How does phishing work?")]
    dirty = [_rec("What is Log4Shell?")]  # same as an eval question
    assert_no_contamination(clean, evalset)  # no raise
    with pytest.raises(ContaminationError):
        assert_no_contamination(dirty, evalset)
