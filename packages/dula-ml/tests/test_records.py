"""Unit tests for SFT record mapping and formatting."""

from __future__ import annotations

from dula_ml.records import SFTRecord, from_raw


def test_from_raw_instruction_output() -> None:
    rec = from_raw({"instruction": "What is T1110?", "output": "Brute force."}, source="primus")
    assert rec is not None
    assert rec.instruction == "What is T1110?"
    assert rec.output == "Brute force."
    assert rec.source == "primus"


def test_from_raw_question_answer_aliases() -> None:
    rec = from_raw({"question": "Q?", "answer": "A."}, source="s")
    assert rec is not None and rec.instruction == "Q?" and rec.output == "A."


def test_from_raw_messages_style() -> None:
    raw = {"messages": [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "yo"}]}
    rec = from_raw(raw, source="s")
    assert rec is not None and rec.instruction == "hi" and rec.output == "yo"


def test_from_raw_sharegpt_conversations() -> None:
    raw = {"conversations": [{"from": "human", "value": "hi"}, {"from": "gpt", "value": "yo"}]}
    rec = from_raw(raw, source="s")
    assert rec is not None and rec.instruction == "hi" and rec.output == "yo"


def test_from_raw_rejects_incomplete() -> None:
    assert from_raw({"instruction": "only"}, source="s") is None
    assert from_raw({"messages": [{"role": "user", "content": "hi"}]}, source="s") is None


def test_to_text_and_messages_have_roles() -> None:
    rec = SFTRecord(instruction="Explain phishing", output="Phishing is...", input="context")
    text = rec.to_text(system="You are Dula")
    assert "<|system|>" in text and "<|user|>" in text and "<|assistant|>" in text
    assert "context" in text
    msgs = rec.to_messages(system="sys")
    assert [m["role"] for m in msgs] == ["system", "user", "assistant"]
