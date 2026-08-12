"""Incident endpoints (docs/12-API/APIStandards.md). AuthZ via OPA; tenant-scoped."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from dula_platform_api.authz import require
from dula_platform_api.db import TenantSession
from dula_platform_api.deps import Context
from dula_platform_api.events import Publisher
from dula_platform_api.schemas import IncidentCreate, IncidentOut, IncidentUpdate, Page
from dula_platform_api.services import IncidentService

router = APIRouter(prefix="/api/v1/incidents", tags=["incidents"])


@router.post(
    "",
    response_model=IncidentOut,
    status_code=201,
    dependencies=[Depends(require("incidents.create", "incident"))],
)
async def create_incident(
    data: IncidentCreate, ctx: Context, session: TenantSession, publisher: Publisher
) -> IncidentOut:
    obj = await IncidentService(session, ctx, publisher).create(data)
    return IncidentOut.model_validate(obj)


@router.get(
    "",
    response_model=Page[IncidentOut],
    dependencies=[Depends(require("incidents.read", "incident"))],
)
async def list_incidents(
    ctx: Context,
    session: TenantSession,
    publisher: Publisher,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Page[IncidentOut]:
    items, total = await IncidentService(session, ctx, publisher).list(limit=limit, offset=offset)
    return Page[IncidentOut](
        items=[IncidentOut.model_validate(i) for i in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{incident_id}",
    response_model=IncidentOut,
    dependencies=[Depends(require("incidents.read", "incident"))],
)
async def get_incident(
    incident_id: uuid.UUID, ctx: Context, session: TenantSession, publisher: Publisher
) -> IncidentOut:
    obj = await IncidentService(session, ctx, publisher).get(incident_id)
    return IncidentOut.model_validate(obj)


@router.patch(
    "/{incident_id}",
    response_model=IncidentOut,
    dependencies=[Depends(require("incidents.update", "incident"))],
)
async def update_incident(
    incident_id: uuid.UUID,
    data: IncidentUpdate,
    ctx: Context,
    session: TenantSession,
    publisher: Publisher,
) -> IncidentOut:
    obj = await IncidentService(session, ctx, publisher).update(incident_id, data)
    return IncidentOut.model_validate(obj)


@router.delete(
    "/{incident_id}",
    status_code=204,
    dependencies=[Depends(require("incidents.delete", "incident"))],
)
async def delete_incident(
    incident_id: uuid.UUID, ctx: Context, session: TenantSession, publisher: Publisher
) -> None:
    await IncidentService(session, ctx, publisher).delete(incident_id)
