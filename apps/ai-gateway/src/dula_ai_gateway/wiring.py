"""Assemble the RAG/gateway subsystem from configuration (offline or backed profile)."""

from __future__ import annotations

from dula_ai.corpus import DEMO_PUBLIC_CORPUS
from dula_ai.embeddings import Embedder, HashingEmbedder, OllamaEmbedder
from dula_ai.factory import RagStack, build_offline_stack
from dula_ai.gateway import AuditHook, LLMGateway
from dula_ai.knowledge import KnowledgeService
from dula_ai.providers import ExtractiveProvider, LLMProvider, OllamaProvider
from dula_ai.rag import RAGService
from dula_ai.retrieval import HybridRetriever
from dula_ai.stores import OpenSearchLexicalStore, QdrantVectorStore

from dula_ai_gateway.config import Settings


def _provider(settings: Settings) -> LLMProvider:
    if settings.provider == "ollama":
        return OllamaProvider(settings.ollama_model, settings.ollama_url)
    return ExtractiveProvider()


def _embedder(settings: Settings) -> Embedder:
    if settings.provider == "ollama":
        return OllamaEmbedder(settings.ollama_embed_model, settings.ollama_url)
    return HashingEmbedder(settings.embedding_dim)


async def build_subsystem(settings: Settings, audit: AuditHook | None) -> RagStack:
    provider = _provider(settings)
    if settings.profile == "offline":
        stack = build_offline_stack(
            embedding_dim=settings.embedding_dim,
            top_k=settings.top_k,
            provider=provider,
            audit=audit,
            max_tokens_per_tenant=settings.max_tokens_per_tenant,
        )
    else:
        embedder = _embedder(settings)
        vector = QdrantVectorStore(settings.qdrant_url, settings.qdrant_collection, embedder.dim)
        await vector.ensure_collection()
        lexical = OpenSearchLexicalStore(settings.opensearch_url, settings.opensearch_index)
        await lexical.ensure_index()
        knowledge = KnowledgeService(vector, lexical, embedder)
        retriever = HybridRetriever(vector, lexical, embedder)
        gateway = LLMGateway(
            provider, audit=audit, max_tokens_per_tenant=settings.max_tokens_per_tenant
        )
        rag = RAGService(retriever, gateway, top_k=settings.top_k)
        stack = RagStack(knowledge, rag, gateway, retriever, vector, lexical, embedder)

    if settings.seed_demo_corpus:
        for doc in DEMO_PUBLIC_CORPUS:
            await stack.knowledge.ingest(doc)
    return stack
