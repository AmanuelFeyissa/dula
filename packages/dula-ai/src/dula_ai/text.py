"""Shared lightweight text utilities (no heavy NLP deps — air-gapped friendly)."""

from __future__ import annotations

import re

_TOKEN_RE = re.compile(r"[a-z0-9]+")

# Small English stopword set — enough to keep relevance/overlap checks focused on content
# words (so an out-of-domain query does not "overlap" a document merely via "the"/"is").
_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "do",
        "does",
        "for",
        "from",
        "how",
        "i",
        "in",
        "is",
        "it",
        "of",
        "on",
        "or",
        "that",
        "the",
        "this",
        "to",
        "what",
        "when",
        "which",
        "who",
        "why",
        "with",
        "you",
        "your",
    }
)


def tokenize(text: str) -> list[str]:
    """Lowercase alphanumeric tokenization used by the offline embedder and lexical store."""
    return _TOKEN_RE.findall(text.lower())


def content_tokens(text: str) -> list[str]:
    """Tokens with stopwords removed — used for relevance gating and reranking."""
    return [t for t in tokenize(text) if t not in _STOPWORDS]


def estimate_tokens(text: str) -> int:
    """Rough token estimate (~4 chars/token) for budget accounting without a tokenizer."""
    return max(1, len(text) // 4)
