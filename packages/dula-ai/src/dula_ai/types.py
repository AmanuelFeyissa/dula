"""Core RAG/gateway value types (docs/03-Architecture/RAGArchitecture.md)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Data classification drives retrieval eligibility & handling (DataSecurity.md).
CLASSIFICATIONS = ("public", "internal", "sensitive")


@dataclass(frozen=True, slots=True)
class Chunk:
    """An indexed unit of knowledge with provenance metadata.

    ``tenant`` is a tenant UUID string, or the sentinel ``"public"`` for shared knowledge
    (ATT&CK/CVE/etc.). Every chunk carries provenance so a poisoned source can be traced and
    purged (T3 — RAG poisoning).
    """

    id: str
    document_id: str
    text: str
    tenant: str
    source: str
    classification: str = "public"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class RetrievedChunk:
    chunk: Chunk
    score: float


@dataclass(frozen=True, slots=True)
class Citation:
    """A grounding reference the model must attribute claims to."""

    marker: int  # 1-based index shown to the model/user as [n]
    chunk_id: str
    document_id: str
    source: str
    snippet: str


@dataclass(frozen=True, slots=True)
class Usage:
    prompt_tokens: int
    completion_tokens: int
    # Which provider actually answered, when routing wasn't static (CanaryProvider). None for
    # every non-canary provider -- this is per-call attribution, distinct from the outer
    # provider's own (static) `.name`, so it survives concurrent calls without shared state.
    routed_provider: str | None = None

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


@dataclass(frozen=True, slots=True)
class Answer:
    text: str
    citations: list[Citation]
    usage: Usage
    model: str
    grounded: bool
