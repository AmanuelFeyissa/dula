"""Knowledge ingestion endpoints — tenant-private documents and source purge."""

from __future__ import annotations

import uuid

from dula_ai.knowledge import Document, LicenseError
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from dula_ai_gateway.deps import Context, Subsystem, require

router = APIRouter(prefix="/api/v1/knowledge", tags=["knowledge"])


class IngestRequest(BaseModel):
    text: str = Field(min_length=1)
    source: str = Field(min_length=1, max_length=255)
    document_id: str | None = None
    license: str = "proprietary"
    classification: str = "internal"


class IngestResponse(BaseModel):
    document_id: str
    chunks: int


@router.post(
    "/documents",
    response_model=IngestResponse,
    status_code=201,
    dependencies=[Depends(require("knowledge.ingest"))],
)
async def ingest(data: IngestRequest, ctx: Context, subsystem: Subsystem) -> IngestResponse:
    """Ingest a document into the caller's **tenant-private** knowledge (never public)."""
    document_id = data.document_id or str(uuid.uuid4())
    doc = Document(
        id=document_id,
        text=data.text,
        source=data.source,
        tenant=ctx.tenant,  # always private to the caller's tenant
        license=data.license,
        classification=data.classification,
    )
    try:
        chunks = await subsystem.knowledge.ingest(doc)
    except LicenseError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return IngestResponse(document_id=document_id, chunks=chunks)


@router.delete(
    "/sources/{source}",
    status_code=204,
    dependencies=[Depends(require("knowledge.purge"))],
)
async def purge_source(source: str, ctx: Context, subsystem: Subsystem) -> None:
    await subsystem.knowledge.purge_source(source)
