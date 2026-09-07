"""Preference-pair record model + formatting for DPO safety-restoration
(docs/08-AI/FineTuningStrategy.md).

A normalized ``(prompt, chosen, rejected)`` preference example with provenance, plus a mapper
for the canonical hh-rlhf shape (full transcripts sharing a prompt prefix, split on the final
``\\n\\nAssistant:`` turn) and a pre-split ``prompt``/``chosen``/``rejected`` shape used by many
DPO-ready dataset mirrors. Kept torch-free, mirroring ``dula_ml.records``, so formatting is
identical in CI and on the GPU runner.

The ``rejected`` field intentionally carries the less-safe response as a *negative* example for
DPO's contrastive loss (the model is never supervised to reproduce it) -- this is the standard,
intended use of harmlessness-preference data such as hh-rlhf's ``harmless-base`` split, and is
not filtered by ``dula_ml.safety`` (which targets single-response SFT rows, not preference
pairs).
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from pydantic import BaseModel, Field

from dula_ml.contamination import ContaminationError
from dula_ml.dedup import content_hash

_ASSISTANT_TURN = "\n\nAssistant:"


class PreferenceRecord(BaseModel):
    """One DPO preference example: a prompt with a preferred and a dispreferred response."""

    prompt: str = Field(min_length=1)
    chosen: str = Field(min_length=1)
    rejected: str = Field(min_length=1)
    source: str = "unknown"
    license: str = "unknown"
    meta: dict[str, Any] = Field(default_factory=dict)


def _split_last_assistant_turn(transcript: str) -> tuple[str, str] | None:
    """Split a full multi-turn transcript into (prompt incl. history, final response)."""
    idx = transcript.rfind(_ASSISTANT_TURN)
    if idx == -1:
        return None
    prompt = transcript[:idx].strip()
    response = transcript[idx + len(_ASSISTANT_TURN) :].strip()
    if not prompt or not response:
        return None
    return prompt, response


def from_hh_rlhf(
    raw: dict[str, Any], *, source: str, license: str = "unknown"
) -> PreferenceRecord | None:
    """Map the canonical hh-rlhf shape: full transcripts sharing a prompt prefix."""
    chosen_raw = raw.get("chosen")
    rejected_raw = raw.get("rejected")
    if not isinstance(chosen_raw, str) or not isinstance(rejected_raw, str):
        return None
    chosen_split = _split_last_assistant_turn(chosen_raw)
    rejected_split = _split_last_assistant_turn(rejected_raw)
    if chosen_split is None or rejected_split is None:
        return None
    prompt, chosen_response = chosen_split
    rejected_prompt, rejected_response = rejected_split
    if prompt != rejected_prompt:
        return None  # transcripts diverge before the final turn -- not a clean pair
    return PreferenceRecord(
        prompt=prompt,
        chosen=chosen_response,
        rejected=rejected_response,
        source=source,
        license=license,
    )


def from_raw(
    raw: dict[str, Any], *, source: str, license: str = "unknown"
) -> PreferenceRecord | None:
    """Map a common preference-pair row: a pre-split ``prompt``/``chosen``/``rejected`` schema,
    or the hh-rlhf raw shape (full transcripts sharing a prompt prefix)."""
    prompt, chosen, rejected = raw.get("prompt"), raw.get("chosen"), raw.get("rejected")
    if (
        isinstance(prompt, str)
        and isinstance(chosen, str)
        and isinstance(rejected, str)
        and prompt
        and chosen
        and rejected
    ):
        return PreferenceRecord(
            prompt=prompt, chosen=chosen, rejected=rejected, source=source, license=license
        )
    return from_hh_rlhf(raw, source=source, license=license)


def dedup(records: Iterable[PreferenceRecord]) -> tuple[list[PreferenceRecord], int]:
    """Return (unique records in first-seen order, number removed) -- exact dedup by content."""
    seen: set[str] = set()
    unique: list[PreferenceRecord] = []
    removed = 0
    for record in records:
        key = content_hash(f"{record.prompt}\n{record.chosen}\n{record.rejected}")
        if key in seen:
            removed += 1
            continue
        seen.add(key)
        unique.append(record)
    return unique, removed


def contamination_overlap(
    records: Iterable[PreferenceRecord], eval_hash_set: set[str]
) -> list[PreferenceRecord]:
    """Return preference records whose prompt matches an eval item."""
    return [r for r in records if content_hash(r.prompt) in eval_hash_set]


def assert_no_contamination(records: Iterable[PreferenceRecord], eval_hash_set: set[str]) -> None:
    overlap = contamination_overlap(records, eval_hash_set)
    if overlap:
        raise ContaminationError(
            f"{len(overlap)} preference records overlap the eval set; refusing to train"
        )
