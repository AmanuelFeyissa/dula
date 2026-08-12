"""Dula AI Gateway service (docs/03-Architecture/AIArchitecture.md).

Exposes grounded Q&A (UC-14) and alert triage (UC-01) over the RAG subsystem behind the
LLM Gateway. Runs fully offline by default (extractive provider + in-memory stores) and can
be pointed at Qdrant/OpenSearch/Ollama via configuration.
"""
