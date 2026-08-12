"""Chunking (docs/08-AI/RAGEngineering.md §1).

Structure-aware-ish splitting: prefer paragraph boundaries, cap chunk size, and overlap to
preserve context across boundaries. Each chunk inherits the document's provenance metadata.
Exact sizes are tuned via retrieval eval (REQUIRES RESEARCH); these defaults are a sane start.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from dula_ai.types import Chunk


@dataclass(frozen=True, slots=True)
class ChunkingConfig:
    max_chars: int = 1000
    overlap_chars: int = 150


def _split_paragraphs(text: str) -> list[str]:
    return [p.strip() for p in text.replace("\r\n", "\n").split("\n\n") if p.strip()]


def _pack(paragraphs: list[str], cfg: ChunkingConfig) -> list[str]:
    chunks: list[str] = []
    current = ""
    for para in paragraphs:
        if len(para) > cfg.max_chars:
            # A single oversized paragraph is windowed with overlap.
            if current:
                chunks.append(current)
                current = ""
            step = cfg.max_chars - cfg.overlap_chars
            for start in range(0, len(para), step):
                chunks.append(para[start : start + cfg.max_chars])
            continue
        if current and len(current) + len(para) + 2 > cfg.max_chars:
            chunks.append(current)
            tail = current[-cfg.overlap_chars :] if cfg.overlap_chars else ""
            current = (tail + "\n\n" + para).strip()
        else:
            current = (current + "\n\n" + para).strip() if current else para
    if current:
        chunks.append(current)
    return chunks


def chunk_document(
    *,
    document_id: str,
    text: str,
    tenant: str,
    source: str,
    classification: str = "public",
    metadata: dict[str, object] | None = None,
    config: ChunkingConfig | None = None,
) -> list[Chunk]:
    """Split a document into provenance-carrying chunks with stable ids."""
    cfg = config or ChunkingConfig()
    pieces = _pack(_split_paragraphs(text), cfg) or ([text.strip()] if text.strip() else [])
    chunks: list[Chunk] = []
    for i, piece in enumerate(pieces):
        digest = hashlib.blake2b(f"{document_id}:{i}:{piece}".encode(), digest_size=8).hexdigest()
        chunks.append(
            Chunk(
                id=f"{document_id}:{i}:{digest}",
                document_id=document_id,
                text=piece,
                tenant=tenant,
                source=source,
                classification=classification,
                metadata={**(metadata or {}), "chunk_index": i},
            )
        )
    return chunks
