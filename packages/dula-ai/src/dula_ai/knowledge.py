"""Knowledge ingestion (docs/08-AI/DatasetStrategy.md, RAGArchitecture.md §2).

Ingest documents into both indices with provenance, enforcing a **license allowlist** for
shared public knowledge (T3/T4 — poisoning & licensing). Sources can be purged by name so a
poisoned source is traceable and removable.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from typing import Any

from dula_ai import PUBLIC_TENANT
from dula_ai.chunking import ChunkingConfig, chunk_document
from dula_ai.embeddings import Embedder
from dula_ai.stores import LexicalStore, VectorStore

# Licenses acceptable for *public/shared* knowledge. Tenant-private data is the tenant's own.
PUBLIC_ALLOWED_LICENSES = frozenset(
    {
        "MIT",
        "Apache-2.0",
        "BSD-3-Clause",
        "CC0-1.0",
        "CC-BY-4.0",
        "CC-BY-SA-4.0",
        "MITRE-ATT&CK",  # ATT&CK terms of use
        "public-domain",
    }
)

# Registry of intended public knowledge sources (ingestion of full feeds is FUTURE).
KNOWLEDGE_SOURCES: dict[str, str] = {
    "mitre-attack": "MITRE-ATT&CK",
    "nvd-cve": "public-domain",
    "cisa-kev": "public-domain",
    "sigma-rules": "CC-BY-4.0",
}


class LicenseError(Exception):
    """Raised when public knowledge is ingested without an allowlisted license."""


@dataclass(frozen=True, slots=True)
class Document:
    id: str
    text: str
    source: str
    tenant: str = PUBLIC_TENANT
    license: str = "public-domain"
    classification: str = "public"
    metadata: dict[str, Any] = field(default_factory=dict)


class KnowledgeService:
    def __init__(
        self,
        vector_store: VectorStore,
        lexical_store: LexicalStore,
        embedder: Embedder,
        *,
        chunking: ChunkingConfig | None = None,
        allowed_licenses: frozenset[str] = PUBLIC_ALLOWED_LICENSES,
    ) -> None:
        self._vectors = vector_store
        self._lexical = lexical_store
        self._embedder = embedder
        self._chunking = chunking
        self._allowed = allowed_licenses

    async def ingest(self, doc: Document) -> int:
        """Chunk, embed, and index a document; return the chunk count (raises on bad license)."""
        if doc.tenant == PUBLIC_TENANT and doc.license not in self._allowed:
            raise LicenseError(f"license '{doc.license}' not allowed for public knowledge")
        chunks = chunk_document(
            document_id=doc.id,
            text=doc.text,
            tenant=doc.tenant,
            source=doc.source,
            classification=doc.classification,
            metadata={
                **doc.metadata,
                "license": doc.license,
                "embedding_model": self._embedder.name,
                "ingested_at": dt.datetime.now(dt.UTC).isoformat(),
            },
            config=self._chunking,
        )
        if not chunks:
            return 0
        vectors = self._embedder.embed([c.text for c in chunks])
        await self._vectors.upsert(chunks, vectors)
        await self._lexical.index(chunks)
        return len(chunks)

    async def purge_source(self, source: str) -> None:
        """Remove all chunks from a source across both indices (poison response — T3)."""
        await self._vectors.delete_by_source(source)
        await self._lexical.delete_by_source(source)
