"""API response schemas for the AI Gateway."""

from __future__ import annotations

from dula_ai.rag import AskResult
from pydantic import BaseModel


class CitationOut(BaseModel):
    marker: int
    source: str
    document_id: str
    snippet: str


class UsageOut(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class AnswerResponse(BaseModel):
    answer: str
    grounded: bool
    model: str
    prompt_version: str
    citations: list[CitationOut]
    usage: UsageOut


def to_response(result: AskResult) -> AnswerResponse:
    ans = result.answer
    return AnswerResponse(
        answer=ans.text,
        grounded=ans.grounded,
        model=ans.model,
        prompt_version=result.prompt_version,
        citations=[
            CitationOut(
                marker=c.marker, source=c.source, document_id=c.document_id, snippet=c.snippet
            )
            for c in ans.citations
        ],
        usage=UsageOut(
            prompt_tokens=ans.usage.prompt_tokens,
            completion_tokens=ans.usage.completion_tokens,
            total_tokens=ans.usage.total_tokens,
        ),
    )
