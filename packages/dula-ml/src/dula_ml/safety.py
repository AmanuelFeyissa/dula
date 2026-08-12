"""Training-data safety filtering (docs/08-AI/DatasetStrategy.md §6, AIThreatModel.md).

A **coarse, conservative** filter that drops examples which teach *operational offensive*
behaviour (building/deploying working attack tooling), while keeping defensive and analytical
security content. It is a first gate, not a substitute for human review — flagged material is
excluded from training, not merely warned about.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

from dula_ml.records import SFTRecord

# Requests whose *compliant* answer would be operational offensive assistance.
_OFFENSIVE_REQUEST = [
    re.compile(
        r"\bwrite (me )?(a )?(working|functional) (exploit|malware|ransomware|keylogger)", re.I
    ),
    re.compile(
        r"\b(create|build|develop|generate) (a )?(malware|ransomware|virus|worm|keylogger|botnet)",
        re.I,
    ),
    re.compile(
        r"\bstep[- ]by[- ]step (guide|instructions) to (hack|breach|compromise|break into)", re.I
    ),
    re.compile(r"\bhow (do i|to) (build|deploy|spread) (malware|ransomware|a botnet)", re.I),
    re.compile(r"\bfully undetectable (payload|malware)", re.I),
]

# Signals the answer actually complied with operational offense (not just discussing it).
_COMPLIANT_OUTPUT = [
    re.compile(r"```[a-z]*\n", re.I),  # a code block in an offensive-request answer
    re.compile(r"\bhere('?s| is) (the|a) (working|complete) (exploit|payload|malware)", re.I),
]


def is_unsafe_training_example(record: SFTRecord) -> bool:
    """True if the record teaches operational offensive tooling and the answer complies."""
    if not any(p.search(record.instruction) for p in _OFFENSIVE_REQUEST):
        return False
    # An offensive request is only unsafe as training data if the output complies.
    return any(p.search(record.output) for p in _COMPLIANT_OUTPUT)


def filter_safe(records: Iterable[SFTRecord]) -> tuple[list[SFTRecord], list[SFTRecord]]:
    """Return (safe records, dropped records)."""
    safe: list[SFTRecord] = []
    dropped: list[SFTRecord] = []
    for record in records:
        (dropped if is_unsafe_training_example(record) else safe).append(record)
    return safe, dropped
