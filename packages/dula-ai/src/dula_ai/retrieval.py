"""Hybrid retrieval (docs/08-AI/RAGEngineering.md §3-5).

Fuse vector (Qdrant) and lexical/BM25 (OpenSearch) candidates with Reciprocal Rank Fusion,
then optionally rerank for precision. Tenant/authorization filtering is applied **at
retrieval** (in the stores) so unauthorized/other-tenant content never reaches the model.
"""

from __future__ import annotations

from typing import Protocol

from dula_ai import PUBLIC_TENANT
from dula_ai.embeddings import Embedder
from dula_ai.stores import LexicalStore, VectorStore
from dula_ai.text import content_tokens, tokenize
from dula_ai.types import RetrievedChunk


class Reranker(Protocol):
    def rerank(self, query: str, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]: ...


class NoopReranker:
    def rerank(self, query: str, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
        return chunks


class LexicalOverlapReranker:
    """Cheap, offline reranker: token-overlap recall of the query in the chunk.

    Stands in for a cross-encoder (REQUIRES RESEARCH) while keeping the pipeline dependency-free.
    """

    def rerank(self, query: str, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
        q = set(content_tokens(query))
        if not q:
            return chunks

        def score(rc: RetrievedChunk) -> float:
            toks = set(tokenize(rc.chunk.text))
            return len(q & toks) / len(q)

        return sorted(chunks, key=score, reverse=True)


def reciprocal_rank_fusion(
    result_lists: list[list[RetrievedChunk]], *, rrf_k: int = 60
) -> list[RetrievedChunk]:
    """Combine ranked lists by RRF; returns fused chunks with fusion scores."""
    scores: dict[str, float] = {}
    best: dict[str, RetrievedChunk] = {}
    for results in result_lists:
        for rank, rc in enumerate(results):
            cid = rc.chunk.id
            scores[cid] = scores.get(cid, 0.0) + 1.0 / (rrf_k + rank + 1)
            best.setdefault(cid, rc)
    fused = [RetrievedChunk(chunk=best[cid].chunk, score=score) for cid, score in scores.items()]
    fused.sort(key=lambda r: r.score, reverse=True)
    return fused


class HybridRetriever:
    def __init__(
        self,
        vector_store: VectorStore,
        lexical_store: LexicalStore,
        embedder: Embedder,
        *,
        reranker: Reranker | None = None,
        rrf_k: int = 60,
    ) -> None:
        self._vectors = vector_store
        self._lexical = lexical_store
        self._embedder = embedder
        self._reranker = reranker or LexicalOverlapReranker()
        self._rrf_k = rrf_k

    async def retrieve(
        self, query: str, *, tenant: str, k: int = 5, candidate_k: int = 20
    ) -> list[RetrievedChunk]:
        tenants = list(dict.fromkeys([tenant, PUBLIC_TENANT]))
        qvec = self._embedder.embed([query])[0]
        vec_hits = await self._vectors.search(qvec, tenants=tenants, k=candidate_k)
        lex_hits = await self._lexical.search(query, tenants=tenants, k=candidate_k)
        fused = reciprocal_rank_fusion([vec_hits, lex_hits], rrf_k=self._rrf_k)
        reranked = self._reranker.rerank(query, fused[:candidate_k])
        return reranked[:k]
