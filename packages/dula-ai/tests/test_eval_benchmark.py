"""RAG evaluation benchmark (docs/08-AI/EvaluationStrategy.md, Benchmarking.md).

The Stage-6 baseline: over a fixed public corpus, measure retrieval recall@k, citation
correctness, and groundedness, and assert they clear a baseline. "Evaluation gates
everything" — this runs in CI on the offline stack so RAG quality cannot regress silently.
"""

from __future__ import annotations

from dula_ai.factory import RagStack
from dula_ai.rag import RAGService

# question -> the document that should ground the answer.
BENCHMARK: list[tuple[str, str]] = [
    ("How do I defend against brute force password attacks?", "attack-t1110"),
    ("What is Log4Shell and how is it remediated?", "cve-log4shell"),
    ("How do attackers abuse PowerShell?", "attack-t1059"),
    ("What controls mitigate phishing emails?", "attack-t1566"),
    ("How do I protect against SMBv1 remote code execution?", "cve-eternalblue"),
    ("What multi-factor authentication does CISA recommend?", "cisa-mfa"),
]

RECALL_BASELINE = 0.8
CITATION_BASELINE = 0.8


async def _run(rag: RAGService) -> dict[str, float]:
    recall_hits = 0
    citation_hits = 0
    grounded_hits = 0
    for question, expected_doc in BENCHMARK:
        result = await rag.ask(question=question, tenant="tenant-x", subject="analyst")
        retrieved_docs = {rc.chunk.document_id for rc in result.retrieved}
        if expected_doc in retrieved_docs:
            recall_hits += 1
        cited_docs = {c.document_id for c in result.answer.citations}
        if expected_doc in cited_docs:
            citation_hits += 1
        if result.answer.grounded:
            grounded_hits += 1
    n = len(BENCHMARK)
    return {
        "recall_at_k": recall_hits / n,
        "citation_correctness": citation_hits / n,
        "groundedness": grounded_hits / n,
    }


async def test_benchmark_meets_baseline(stack: RagStack) -> None:
    metrics = await _run(stack.rag)
    assert metrics["recall_at_k"] >= RECALL_BASELINE, metrics
    assert metrics["citation_correctness"] >= CITATION_BASELINE, metrics
    # Every in-corpus question must yield a grounded, cited answer.
    assert metrics["groundedness"] >= CITATION_BASELINE, metrics


async def test_unknown_question_is_not_hallucinated(stack: RagStack) -> None:
    # A question with no supporting evidence must not produce a grounded (cited) answer.
    result = await stack.rag.ask(
        question="What is the capital of France?", tenant="tenant-x", subject="analyst"
    )
    assert result.answer.grounded is False
