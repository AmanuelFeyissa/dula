"""Embeddings (docs/08-AI/RAGEngineering.md §2).

Embedders are pluggable. The default `HashingEmbedder` is a deterministic feature-hashing
vectorizer with **no model download and no network** — it keeps RAG working offline/air-gapped
and makes tests reproducible. Production swaps in a self-hostable semantic model (bge/e5/gte —
REQUIRES RESEARCH, ADR-0007 scope) via `OllamaEmbedder` or a sentence-transformers adapter;
the embedding model version is recorded because changing it requires re-embedding.
"""

from __future__ import annotations

import hashlib
import math
from typing import Protocol

from dula_ai.text import tokenize


class Embedder(Protocol):
    name: str

    @property
    def dim(self) -> int: ...

    def embed(self, texts: list[str]) -> list[list[float]]: ...


def cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b, strict=True))


class HashingEmbedder:
    """Deterministic signed feature-hashing embedder, L2-normalized (offline default)."""

    def __init__(self, dim: int = 256) -> None:
        self._dim = dim
        self.name = f"hashing-{dim}"

    @property
    def dim(self) -> int:
        return self._dim

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._vec(t) for t in texts]

    def _vec(self, text: str) -> list[float]:
        v = [0.0] * self._dim
        for tok in tokenize(text):
            h = int(hashlib.blake2b(tok.encode(), digest_size=8).hexdigest(), 16)
            v[h % self._dim] += 1.0 if (h >> 8) & 1 else -1.0
        norm = math.sqrt(sum(x * x for x in v)) or 1.0
        return [x / norm for x in v]


class OllamaEmbedder:
    """Embeddings via a local Ollama server (ADR-0005 dev serving). Optional, not offline-free.

    Kept import-light; `httpx` is only used when `embed` is called.
    """

    def __init__(
        self, model: str, base_url: str = "http://localhost:11434", dim: int = 768
    ) -> None:
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._dim = dim
        self.name = f"ollama-{model}"

    @property
    def dim(self) -> int:
        return self._dim

    def embed(self, texts: list[str]) -> list[list[float]]:
        import httpx

        out: list[list[float]] = []
        with httpx.Client(timeout=30.0) as client:
            for text in texts:
                resp = client.post(
                    f"{self._base_url}/api/embeddings",
                    json={"model": self._model, "prompt": text},
                )
                resp.raise_for_status()
                out.append([float(x) for x in resp.json()["embedding"]])
        return out
