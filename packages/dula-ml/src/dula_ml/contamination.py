"""Benchmark contamination control (docs/08-AI/DatasetStrategy.md §5, Benchmarking.md).

The held-out eval/benchmark set must never appear in training data. Training pipelines assert
zero overlap by hashing; a non-zero overlap is a hard failure (contamination = 0 is a Phase 04
acceptance requirement).
"""

from __future__ import annotations

from collections.abc import Iterable

from dula_ml.dedup import content_hash
from dula_ml.records import SFTRecord


class ContaminationError(Exception):
    """Raised when training data overlaps the eval/benchmark set."""


def eval_hashes(eval_texts: Iterable[str]) -> set[str]:
    """Hash the eval questions/prompts to compare against training inputs."""
    return {content_hash(t) for t in eval_texts}


def contamination_overlap(records: Iterable[SFTRecord], eval_hash_set: set[str]) -> list[SFTRecord]:
    """Return training records whose instruction matches an eval item."""
    return [r for r in records if content_hash(r.instruction) in eval_hash_set]


def assert_no_contamination(records: Iterable[SFTRecord], eval_hash_set: set[str]) -> None:
    overlap = contamination_overlap(records, eval_hash_set)
    if overlap:
        raise ContaminationError(
            f"{len(overlap)} training records overlap the eval set; refusing to train"
        )
