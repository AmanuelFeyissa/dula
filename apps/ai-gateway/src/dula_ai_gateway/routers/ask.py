"""Grounded Q&A endpoints (UC-14), including SSE streaming for the chat UI."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator

from dula_ai.gateway import BudgetExceeded
from dula_ai.rag import AskResult, GuardrailError
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from dula_ai_gateway.deps import Context, Subsystem, require
from dula_ai_gateway.schemas import AnswerResponse, to_response

router = APIRouter(prefix="/api/v1", tags=["ai"])


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=8000)


async def _run(subsystem: Subsystem, ctx: Context, question: str) -> AskResult:
    try:
        return await subsystem.rag.ask(question=question, tenant=ctx.tenant, subject=ctx.subject)
    except GuardrailError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except BudgetExceeded as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc)) from exc


@router.post("/ask", response_model=AnswerResponse, dependencies=[Depends(require("ai.ask"))])
async def ask(data: AskRequest, ctx: Context, subsystem: Subsystem) -> AnswerResponse:
    return to_response(await _run(subsystem, ctx, data.question))


@router.post("/ask/stream", dependencies=[Depends(require("ai.ask"))])
async def ask_stream(data: AskRequest, ctx: Context, subsystem: Subsystem) -> StreamingResponse:
    # Errors (guardrail/budget) surface before streaming begins.
    result = await _run(subsystem, ctx, data.question)

    async def events() -> AsyncIterator[str]:
        for word in result.answer.text.split(" "):
            yield f"data: {json.dumps({'token': word + ' '})}\n\n"
        payload = to_response(result).model_dump()
        yield f"event: done\ndata: {json.dumps(payload)}\n\n"

    return StreamingResponse(events(), media_type="text/event-stream")
