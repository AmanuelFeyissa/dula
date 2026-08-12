"""RAG service (docs/03-Architecture/RAGArchitecture.md, RAGEngineering.md).

Orchestrates the grounded AI request lifecycle: input guardrail → tenant-scoped retrieval →
citation assembly → gateway generation → output guardrail (citation enforcement). Delivers
UC-14 (grounded Q&A) and UC-01 (alert triage) with citations. All retrieved content is treated
as untrusted evidence.
"""

from __future__ import annotations

from dataclasses import dataclass

from dula_ai import guardrails
from dula_ai.gateway import LLMGateway
from dula_ai.prompts import PROMPT_VERSION, build_qa_prompt, build_triage_prompt
from dula_ai.retrieval import HybridRetriever
from dula_ai.text import content_tokens, tokenize
from dula_ai.types import Answer, Citation, RetrievedChunk

_SNIPPET_MAX = 500


def _filter_relevant(query: str, retrieved: list[RetrievedChunk]) -> list[RetrievedChunk]:
    """Relevance floor: keep only chunks sharing at least one term with the query.

    Prevents grounding an answer on top-k chunks that are not actually about the question
    (offline retrieval always returns *something*), which would otherwise let out-of-domain
    questions produce spuriously "cited" answers (T12 — misinformation).
    """
    q = set(content_tokens(query))
    if not q:
        return []
    return [rc for rc in retrieved if q & set(tokenize(rc.chunk.text))]


class GuardrailError(Exception):
    """Raised when the input guardrail rejects a request (mapped to HTTP 400 by callers)."""


@dataclass(frozen=True, slots=True)
class AskResult:
    answer: Answer
    retrieved: list[RetrievedChunk]
    prompt_version: str = PROMPT_VERSION


def _citations(retrieved: list[RetrievedChunk]) -> list[Citation]:
    return [
        Citation(
            marker=i + 1,
            chunk_id=rc.chunk.id,
            document_id=rc.chunk.document_id,
            source=rc.chunk.source,
            snippet=rc.chunk.text[:_SNIPPET_MAX],
        )
        for i, rc in enumerate(retrieved)
    ]


class RAGService:
    def __init__(self, retriever: HybridRetriever, gateway: LLMGateway, *, top_k: int = 5) -> None:
        self._retriever = retriever
        self._gateway = gateway
        self._top_k = top_k

    async def ask(self, *, question: str, tenant: str, subject: str) -> AskResult:
        return await self._run(query=question, tenant=tenant, subject=subject, task="qa")

    async def triage(self, *, alert_summary: str, tenant: str, subject: str) -> AskResult:
        return await self._run(query=alert_summary, tenant=tenant, subject=subject, task="triage")

    async def _run(self, *, query: str, tenant: str, subject: str, task: str) -> AskResult:
        guard = guardrails.check_input(query)
        if not guard.allowed:
            raise GuardrailError(guard.reason or "input rejected")

        retrieved = _filter_relevant(
            query, await self._retriever.retrieve(query, tenant=tenant, k=self._top_k)
        )
        citations = _citations(retrieved)
        if task == "triage":
            system, user = build_triage_prompt(query, citations)
        else:
            system, user = build_qa_prompt(query, citations)

        result = await self._gateway.generate(
            tenant=tenant,
            subject=subject,
            task=task,
            system=system,
            user=user,
            input_flags=guard.flags,
        )

        out = guardrails.check_output(result.text, citations, require_citation=True)
        text = (
            result.text if out.allowed else "I cannot provide a grounded answer for this request."
        )
        used = guardrails.referenced_citations(text, citations)
        answer = Answer(
            text=text,
            citations=used,
            usage=result.usage,
            model=result.model,
            grounded=out.allowed and bool(used),
        )
        return AskResult(answer=answer, retrieved=retrieved)
