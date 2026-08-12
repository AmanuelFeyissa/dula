"""Shared fixtures: a fully in-memory, offline RAG stack seeded with the demo corpus."""

from __future__ import annotations

import pytest
from dula_ai.corpus import DEMO_PUBLIC_CORPUS
from dula_ai.factory import RagStack, build_offline_stack


@pytest.fixture
async def stack() -> RagStack:
    s = build_offline_stack(top_k=3)
    for doc in DEMO_PUBLIC_CORPUS:
        await s.knowledge.ingest(doc)
    return s
