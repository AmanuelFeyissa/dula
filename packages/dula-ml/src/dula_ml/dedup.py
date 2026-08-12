"""Deduplication (docs/08-AI/DatasetStrategy.md §2).

Exact, order-stable dedup by a normalized content hash. Near-duplicate detection (MinHash/
embeddings) is a future enhancement; exact dedup already removes the most common leakage and
inflation from repeated corpus rows.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Iterable

from dula_ml.records import SFTRecord

_WS = re.compile(r"\s+")


def normalize(text: str) -> str:
    return _WS.sub(" ", text).strip().lower()


def content_hash(text: str) -> str:
    return hashlib.sha256(normalize(text).encode("utf-8")).hexdigest()


def record_key(record: SFTRecord) -> str:
    return content_hash(f"{record.instruction}\n{record.input}\n{record.output}")


def dedup(records: Iterable[SFTRecord]) -> tuple[list[SFTRecord], int]:
    """Return (unique records in first-seen order, number removed)."""
    seen: set[str] = set()
    unique: list[SFTRecord] = []
    removed = 0
    for record in records:
        key = record_key(record)
        if key in seen:
            removed += 1
            continue
        seen.add(key)
        unique.append(record)
    return unique, removed
