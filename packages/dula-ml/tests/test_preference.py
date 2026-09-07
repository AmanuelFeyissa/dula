"""Unit tests for preference-pair records (DPO safety-restoration data)."""

from __future__ import annotations

import pytest
from dula_ml.contamination import ContaminationError, eval_hashes
from dula_ml.preference import (
    PreferenceRecord,
    assert_no_contamination,
    dedup,
    from_hh_rlhf,
    from_raw,
)


def test_from_raw_prefers_presplit_schema() -> None:
    raw = {
        "prompt": "How do I pick a lock?",
        "chosen": "I can't help with that.",
        "rejected": "Sure, here's how.",
    }
    rec = from_raw(raw, source="test", license="MIT")
    assert rec == PreferenceRecord(
        prompt="How do I pick a lock?",
        chosen="I can't help with that.",
        rejected="Sure, here's how.",
        source="test",
        license="MIT",
    )


def test_from_hh_rlhf_splits_shared_prompt_on_last_assistant_turn() -> None:
    shared = "\n\nHuman: How do I pick a lock?"
    raw = {
        "chosen": f"{shared}\n\nAssistant: I can't help with that.",
        "rejected": f"{shared}\n\nAssistant: Sure, here's how.",
    }
    rec = from_hh_rlhf(raw, source="hh-rlhf/harmless-base", license="MIT")
    assert rec is not None
    assert rec.prompt == shared.strip()
    assert rec.chosen == "I can't help with that."
    assert rec.rejected == "Sure, here's how."


def test_from_hh_rlhf_rejects_diverging_prompts() -> None:
    raw = {
        "chosen": "\n\nHuman: Question A\n\nAssistant: Answer A",
        "rejected": "\n\nHuman: Question B\n\nAssistant: Answer B",
    }
    assert from_hh_rlhf(raw, source="test") is None


def test_from_hh_rlhf_rejects_missing_assistant_turn() -> None:
    raw = {"chosen": "no assistant marker here", "rejected": "\n\nHuman: Q\n\nAssistant: A"}
    assert from_hh_rlhf(raw, source="test") is None


def test_from_raw_falls_back_to_hh_rlhf_shape() -> None:
    shared = "\n\nHuman: Q"
    raw = {"chosen": f"{shared}\n\nAssistant: safe", "rejected": f"{shared}\n\nAssistant: unsafe"}
    rec = from_raw(raw, source="test")
    assert rec is not None
    assert rec.chosen == "safe"
    assert rec.rejected == "unsafe"


def test_dedup_removes_exact_duplicates_preserving_order() -> None:
    a = PreferenceRecord(prompt="p1", chosen="c", rejected="r")
    b = PreferenceRecord(prompt="p2", chosen="c", rejected="r")
    a_again = PreferenceRecord(prompt="p1", chosen="c", rejected="r")
    unique, removed = dedup([a, b, a_again])
    assert [r.prompt for r in unique] == ["p1", "p2"]
    assert removed == 1


def test_contamination_detected_and_raises() -> None:
    evalset = eval_hashes(["What is Log4Shell?"])
    clean = [PreferenceRecord(prompt="How does phishing work?", chosen="c", rejected="r")]
    dirty = [PreferenceRecord(prompt="What is Log4Shell?", chosen="c", rejected="r")]
    assert_no_contamination(clean, evalset)  # no raise
    with pytest.raises(ContaminationError):
        assert_no_contamination(dirty, evalset)
