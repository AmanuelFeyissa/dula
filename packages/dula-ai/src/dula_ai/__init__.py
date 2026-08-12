"""Dula AI subsystem — the model-agnostic **LLM Gateway** and **RAG** engineering.

This is the platform's AI *plumbing* (docs/03-Architecture/AIArchitecture.md,
RAGArchitecture.md), distinct from **Dula AI** the model (Product 2), which is served behind
the gateway like any other model. Everything here runs **fully offline** by default: the
`HashingEmbedder`, in-memory stores, and the extractive provider need no downloads or network,
so RAG works in air-gapped deployments; real backends (Qdrant, OpenSearch, Ollama) plug in via
configuration.

Core stance (docs/10-Security/AIThreatModel.md): **all retrieved content and all model output
are untrusted**; tenant + authorization filtering happens *at retrieval*.
"""

PUBLIC_TENANT = "public"
