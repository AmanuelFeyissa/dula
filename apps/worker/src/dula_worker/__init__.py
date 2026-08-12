"""Dula event worker (docs/03-Architecture/DataArchitecture.md §2).

Consumes ``domain.entity.action`` events from Redpanda and processes them idempotently
(dedupe by ``event.id``), the substrate that RAG/AI enrichment will build on.
"""
