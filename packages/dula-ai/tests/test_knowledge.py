"""Unit tests for knowledge ingestion, licensing, and purge."""

from __future__ import annotations

import pytest
from dula_ai.factory import RagStack
from dula_ai.knowledge import Document, LicenseError


async def test_public_ingest_requires_allowlisted_license(stack: RagStack) -> None:
    with pytest.raises(LicenseError):
        await stack.knowledge.ingest(
            Document(id="bad", text="some text", source="x", license="GPL-3.0-only")
        )


async def test_tenant_private_ingest_allows_any_license(stack: RagStack) -> None:
    n = await stack.knowledge.ingest(
        Document(
            id="tenant-doc",
            text="internal note about our servers",
            source="upload",
            tenant="tenant-a",
            license="proprietary",
            classification="internal",
        )
    )
    assert n >= 1


async def test_purge_source_removes_from_both_indices(stack: RagStack) -> None:
    hits_before = await stack.retriever.retrieve("phishing spearphishing", tenant="t1", k=3)
    assert any(h.chunk.source == "mitre-attack" for h in hits_before)

    await stack.knowledge.purge_source("mitre-attack")

    lex = await stack.lexical.search("phishing", tenants=["public"], k=5)
    assert all(h.chunk.source != "mitre-attack" for h in lex)
