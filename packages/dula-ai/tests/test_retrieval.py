"""Unit tests for embeddings, fusion, and tenant-scoped hybrid retrieval."""

from __future__ import annotations

from dula_ai.embeddings import HashingEmbedder, cosine
from dula_ai.factory import RagStack
from dula_ai.retrieval import reciprocal_rank_fusion
from dula_ai.types import Chunk, RetrievedChunk


def test_hashing_embedder_is_deterministic_and_normalized() -> None:
    emb = HashingEmbedder(128)
    a = emb.embed(["brute force attack"])[0]
    b = emb.embed(["brute force attack"])[0]
    assert a == b
    assert abs(cosine(a, a) - 1.0) < 1e-9


def _rc(cid: str) -> RetrievedChunk:
    return RetrievedChunk(
        chunk=Chunk(id=cid, document_id=cid, text="t", tenant="public", source="s"), score=1.0
    )


def test_rrf_rewards_agreement_across_lists() -> None:
    vec = [_rc("a"), _rc("b"), _rc("c")]
    lex = [_rc("b"), _rc("a"), _rc("d")]
    fused = reciprocal_rank_fusion([vec, lex])
    # "a" and "b" appear high in both lists and should top the fusion.
    assert {fused[0].chunk.id, fused[1].chunk.id} == {"a", "b"}


async def test_retrieval_finds_relevant_public_docs(stack: RagStack) -> None:
    hits = await stack.retriever.retrieve("Log4Shell remote code execution", tenant="t1", k=3)
    assert any(h.chunk.document_id == "cve-log4shell" for h in hits)


async def test_retrieval_is_tenant_scoped(stack: RagStack) -> None:
    # Ingest a private doc for tenant A; tenant B must never retrieve it.
    from dula_ai.knowledge import Document

    await stack.knowledge.ingest(
        Document(
            id="secret-a",
            text="Tenant A internal runbook: the crown-jewels database is db-prod-7.",
            source="tenant-upload",
            tenant="tenant-a",
            license="proprietary",
            classification="sensitive",
        )
    )
    a_hits = await stack.retriever.retrieve("crown jewels database", tenant="tenant-a", k=5)
    b_hits = await stack.retriever.retrieve("crown jewels database", tenant="tenant-b", k=5)
    assert any(h.chunk.document_id == "secret-a" for h in a_hits)
    assert all(h.chunk.tenant in ("tenant-b", "public") for h in b_hits)
    assert all(h.chunk.document_id != "secret-a" for h in b_hits)
