"""Unit tests for chunking."""

from __future__ import annotations

from dula_ai.chunking import ChunkingConfig, chunk_document


def test_short_document_single_chunk() -> None:
    chunks = chunk_document(
        document_id="d1", text="a short paragraph.", tenant="public", source="s"
    )
    assert len(chunks) == 1
    assert chunks[0].document_id == "d1"
    assert chunks[0].metadata["chunk_index"] == 0


def test_large_paragraph_is_windowed_with_overlap() -> None:
    text = "x" * 2500
    chunks = chunk_document(
        document_id="d2",
        text=text,
        tenant="public",
        source="s",
        config=ChunkingConfig(max_chars=1000, overlap_chars=150),
    )
    assert len(chunks) >= 3
    assert all(len(c.text) <= 1000 for c in chunks)


def test_chunk_ids_are_stable_and_unique() -> None:
    text = "para one.\n\npara two.\n\npara three."
    a = chunk_document(document_id="d3", text=text, tenant="public", source="s")
    b = chunk_document(document_id="d3", text=text, tenant="public", source="s")
    assert [c.id for c in a] == [c.id for c in b]
    assert len({c.id for c in a}) == len(a)
