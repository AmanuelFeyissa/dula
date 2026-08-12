"""Knowledge stores (docs/03-Architecture/RAGArchitecture.md §2, ADR-0003).

Two indices back **hybrid search**: a vector store (Qdrant) and a lexical/BM25 store
(OpenSearch). Both are behind protocols with offline in-memory implementations so the whole
RAG pipeline is testable and air-gapped by default; the Qdrant/OpenSearch adapters are
lazy-imported and used when configured.

**Tenant isolation is enforced here at query time**: every search filters to the caller's
tenant plus shared ``public`` knowledge — a user can never retrieve another tenant's content
(T14 / OWASP LLM08).
"""

from __future__ import annotations

import math
import uuid
from collections import defaultdict
from typing import Any, Protocol

from dula_ai.embeddings import cosine
from dula_ai.text import tokenize
from dula_ai.types import Chunk, RetrievedChunk


class VectorStore(Protocol):
    async def upsert(self, chunks: list[Chunk], vectors: list[list[float]]) -> None: ...
    async def search(
        self, vector: list[float], *, tenants: list[str], k: int
    ) -> list[RetrievedChunk]: ...
    async def delete_by_source(self, source: str) -> int: ...


class LexicalStore(Protocol):
    async def index(self, chunks: list[Chunk]) -> None: ...
    async def search(self, query: str, *, tenants: list[str], k: int) -> list[RetrievedChunk]: ...
    async def delete_by_source(self, source: str) -> int: ...


# --- Offline in-memory implementations -------------------------------------------------


class InMemoryVectorStore:
    def __init__(self) -> None:
        self._items: dict[str, tuple[Chunk, list[float]]] = {}

    async def upsert(self, chunks: list[Chunk], vectors: list[list[float]]) -> None:
        for chunk, vec in zip(chunks, vectors, strict=True):
            self._items[chunk.id] = (chunk, vec)

    async def search(
        self, vector: list[float], *, tenants: list[str], k: int
    ) -> list[RetrievedChunk]:
        scored = [
            RetrievedChunk(chunk=chunk, score=cosine(vector, vec))
            for chunk, vec in self._items.values()
            if chunk.tenant in tenants
        ]
        scored.sort(key=lambda r: r.score, reverse=True)
        return scored[:k]

    async def delete_by_source(self, source: str) -> int:
        victims = [cid for cid, (chunk, _) in self._items.items() if chunk.source == source]
        for cid in victims:
            del self._items[cid]
        return len(victims)


class InMemoryLexicalStore:
    """A compact BM25 index (k1=1.5, b=0.75) — real lexical scoring, no dependencies."""

    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        self._k1 = k1
        self._b = b
        self._chunks: dict[str, Chunk] = {}
        self._tokens: dict[str, list[str]] = {}

    async def index(self, chunks: list[Chunk]) -> None:
        for chunk in chunks:
            self._chunks[chunk.id] = chunk
            self._tokens[chunk.id] = tokenize(chunk.text)

    async def search(self, query: str, *, tenants: list[str], k: int) -> list[RetrievedChunk]:
        ids = [cid for cid, c in self._chunks.items() if c.tenant in tenants]
        if not ids:
            return []
        n = len(ids)
        avgdl = sum(len(self._tokens[cid]) for cid in ids) / n
        df: dict[str, int] = defaultdict(int)
        for cid in ids:
            for term in set(self._tokens[cid]):
                df[term] += 1
        q_terms = tokenize(query)
        scored: list[RetrievedChunk] = []
        for cid in ids:
            toks = self._tokens[cid]
            dl = len(toks) or 1
            tf: dict[str, int] = defaultdict(int)
            for t in toks:
                tf[t] += 1
            score = 0.0
            for term in q_terms:
                if term not in tf:
                    continue
                idf = math.log(1 + (n - df[term] + 0.5) / (df[term] + 0.5))
                denom = tf[term] + self._k1 * (1 - self._b + self._b * dl / avgdl)
                score += idf * (tf[term] * (self._k1 + 1)) / denom
            if score > 0:
                scored.append(RetrievedChunk(chunk=self._chunks[cid], score=score))
        scored.sort(key=lambda r: r.score, reverse=True)
        return scored[:k]

    async def delete_by_source(self, source: str) -> int:
        victims = [cid for cid, c in self._chunks.items() if c.source == source]
        for cid in victims:
            del self._chunks[cid]
            del self._tokens[cid]
        return len(victims)


# --- Real adapters (lazy-imported) -----------------------------------------------------

_QDRANT_NS = uuid.UUID("6f1a2b3c-4d5e-6f70-8192-a3b4c5d6e7f8")


def _payload(chunk: Chunk) -> dict[str, Any]:
    return {
        "chunk_id": chunk.id,
        "document_id": chunk.document_id,
        "text": chunk.text,
        "tenant": chunk.tenant,
        "source": chunk.source,
        "classification": chunk.classification,
        "metadata": chunk.metadata,
    }


def _chunk_from_payload(payload: dict[str, Any]) -> Chunk:
    return Chunk(
        id=payload["chunk_id"],
        document_id=payload["document_id"],
        text=payload["text"],
        tenant=payload["tenant"],
        source=payload["source"],
        classification=payload.get("classification", "public"),
        metadata=payload.get("metadata", {}),
    )


class QdrantVectorStore:
    """Qdrant-backed vector store (ADR-0003). Tenant filtering via payload match."""

    def __init__(self, url: str, collection: str, dim: int) -> None:
        from qdrant_client import AsyncQdrantClient

        self._client = AsyncQdrantClient(url=url)
        self._collection = collection
        self._dim = dim

    async def ensure_collection(self) -> None:
        from qdrant_client import models

        if not await self._client.collection_exists(self._collection):
            await self._client.create_collection(
                self._collection,
                vectors_config=models.VectorParams(size=self._dim, distance=models.Distance.COSINE),
            )
            await self._client.create_payload_index(
                self._collection,
                field_name="tenant",
                field_schema=models.PayloadSchemaType.KEYWORD,
            )
            await self._client.create_payload_index(
                self._collection,
                field_name="source",
                field_schema=models.PayloadSchemaType.KEYWORD,
            )

    async def upsert(self, chunks: list[Chunk], vectors: list[list[float]]) -> None:
        from qdrant_client import models

        points = [
            models.PointStruct(
                id=str(uuid.uuid5(_QDRANT_NS, chunk.id)), vector=vec, payload=_payload(chunk)
            )
            for chunk, vec in zip(chunks, vectors, strict=True)
        ]
        await self._client.upsert(self._collection, points=points)

    async def search(
        self, vector: list[float], *, tenants: list[str], k: int
    ) -> list[RetrievedChunk]:
        from qdrant_client import models

        flt = models.Filter(
            must=[models.FieldCondition(key="tenant", match=models.MatchAny(any=tenants))]
        )
        hits = await self._client.query_points(
            self._collection, query=vector, query_filter=flt, limit=k, with_payload=True
        )
        return [
            RetrievedChunk(chunk=_chunk_from_payload(dict(h.payload or {})), score=float(h.score))
            for h in hits.points
        ]

    async def delete_by_source(self, source: str) -> int:
        from qdrant_client import models

        await self._client.delete(
            self._collection,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(key="source", match=models.MatchValue(value=source))
                    ]
                )
            ),
        )
        return 0  # Qdrant delete does not return a count; caller relies on re-query if needed.


class OpenSearchLexicalStore:
    """OpenSearch BM25 lexical store (ADR-0003). Tenant filtering via term filter."""

    def __init__(self, url: str, index: str) -> None:
        from opensearchpy import AsyncOpenSearch

        self._client = AsyncOpenSearch(hosts=[url])
        self._index = index

    async def ensure_index(self) -> None:
        if not await self._client.indices.exists(index=self._index):
            await self._client.indices.create(
                index=self._index,
                body={
                    "mappings": {
                        "properties": {
                            "chunk_id": {"type": "keyword"},
                            "document_id": {"type": "keyword"},
                            "text": {"type": "text"},
                            "tenant": {"type": "keyword"},
                            "source": {"type": "keyword"},
                            "classification": {"type": "keyword"},
                        }
                    }
                },
            )

    async def index(self, chunks: list[Chunk]) -> None:
        for chunk in chunks:
            await self._client.index(
                index=self._index, id=chunk.id, body=_payload(chunk), refresh=True
            )

    async def search(self, query: str, *, tenants: list[str], k: int) -> list[RetrievedChunk]:
        body = {
            "size": k,
            "query": {
                "bool": {
                    "must": {"match": {"text": query}},
                    "filter": {"terms": {"tenant": tenants}},
                }
            },
        }
        resp = await self._client.search(index=self._index, body=body)
        hits = resp.get("hits", {}).get("hits", [])
        return [
            RetrievedChunk(chunk=_chunk_from_payload(h["_source"]), score=float(h["_score"]))
            for h in hits
        ]

    async def delete_by_source(self, source: str) -> int:
        resp = await self._client.delete_by_query(
            index=self._index, body={"query": {"term": {"source": source}}}, refresh=True
        )
        return int(resp.get("deleted", 0))
