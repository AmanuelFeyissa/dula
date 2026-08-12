"""Factory for a fully in-memory, offline RAG stack.

Assembles the whole subsystem (embedder → stores → retriever → gateway → RAG/knowledge)
using only offline components. The `apps/ai-gateway` service uses this for its air-gapped
default profile, demos use it, and tests build on it — one place that wires the pieces
together correctly.
"""

from __future__ import annotations

from dataclasses import dataclass

from dula_ai.embeddings import Embedder, HashingEmbedder
from dula_ai.gateway import AuditHook, LLMGateway
from dula_ai.knowledge import KnowledgeService
from dula_ai.providers import ExtractiveProvider, LLMProvider
from dula_ai.rag import RAGService
from dula_ai.retrieval import HybridRetriever
from dula_ai.stores import InMemoryLexicalStore, InMemoryVectorStore, LexicalStore, VectorStore


@dataclass
class RagStack:
    knowledge: KnowledgeService
    rag: RAGService
    gateway: LLMGateway
    retriever: HybridRetriever
    vector: VectorStore
    lexical: LexicalStore
    embedder: Embedder


def build_offline_stack(
    *,
    embedding_dim: int = 256,
    top_k: int = 5,
    provider: LLMProvider | None = None,
    audit: AuditHook | None = None,
    max_tokens_per_tenant: int = 200_000,
) -> RagStack:
    embedder = HashingEmbedder(embedding_dim)
    vector = InMemoryVectorStore()
    lexical = InMemoryLexicalStore()
    knowledge = KnowledgeService(vector, lexical, embedder)
    retriever = HybridRetriever(vector, lexical, embedder)
    gateway = LLMGateway(
        provider or ExtractiveProvider(),
        audit=audit,
        max_tokens_per_tenant=max_tokens_per_tenant,
    )
    rag = RAGService(retriever, gateway, top_k=top_k)
    return RagStack(knowledge, rag, gateway, retriever, vector, lexical, embedder)
