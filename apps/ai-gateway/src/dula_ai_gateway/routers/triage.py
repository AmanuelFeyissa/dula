"""Alert triage endpoint (UC-01): grounded triage of an alert."""

from __future__ import annotations

from dula_ai.gateway import BudgetExceeded
from dula_ai.rag import GuardrailError
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from dula_ai_gateway.deps import Context, Subsystem, require
from dula_ai_gateway.schemas import AnswerResponse, to_response

router = APIRouter(prefix="/api/v1", tags=["ai"])


class TriageRequest(BaseModel):
    title: str = Field(min_length=1, max_length=512)
    description: str | None = Field(default=None, max_length=8000)
    severity: str | None = Field(default=None, max_length=16)


def _summary(req: TriageRequest) -> str:
    parts = [f"Title: {req.title}"]
    if req.severity:
        parts.append(f"Severity: {req.severity}")
    if req.description:
        parts.append(f"Details: {req.description}")
    return "\n".join(parts)


@router.post("/triage", response_model=AnswerResponse, dependencies=[Depends(require("ai.triage"))])
async def triage(data: TriageRequest, ctx: Context, subsystem: Subsystem) -> AnswerResponse:
    try:
        result = await subsystem.rag.triage(
            alert_summary=_summary(data), tenant=ctx.tenant, subject=ctx.subject
        )
    except GuardrailError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except BudgetExceeded as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc)) from exc
    return to_response(result)
