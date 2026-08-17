"""Alert endpoints (docs/12-API/APIStandards.md). AuthZ via OPA; tenant-scoped."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from dula_platform_api.authz import require
from dula_platform_api.db import TenantSession
from dula_platform_api.deps import Context
from dula_platform_api.events import Publisher
from dula_platform_api.models import AlertStatus, Severity
from dula_platform_api.schemas import AlertCreate, AlertOut, AlertUpdate, Page
from dula_platform_api.services import AlertService

router = APIRouter(prefix="/api/v1/alerts", tags=["alerts"])


@router.post(
    "",
    response_model=AlertOut,
    status_code=201,
    dependencies=[Depends(require("alerts.create", "alert"))],
)
async def create_alert(
    data: AlertCreate, ctx: Context, session: TenantSession, publisher: Publisher
) -> AlertOut:
    obj = await AlertService(session, ctx, publisher).create(data)
    return AlertOut.model_validate(obj)


@router.get(
    "", response_model=Page[AlertOut], dependencies=[Depends(require("alerts.read", "alert"))]
)
async def list_alerts(
    ctx: Context,
    session: TenantSession,
    publisher: Publisher,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    q: Annotated[str | None, Query(max_length=200)] = None,
    severity: Severity | None = None,
    status: AlertStatus | None = None,
    sort: Annotated[str | None, Query(max_length=32)] = None,
) -> Page[AlertOut]:
    # severity/status are enums, so FastAPI already rejects an unrecognised value with 422
    # before this body runs — no separate validation needed for them.
    equals = {
        k: v.value for k, v in {"severity": severity, "status": status}.items() if v is not None
    }
    items, total = await AlertService(session, ctx, publisher).list(
        limit=limit, offset=offset, q=q, sort=sort, equals=equals or None
    )
    return Page[AlertOut](
        items=[AlertOut.model_validate(a) for a in items], total=total, limit=limit, offset=offset
    )


@router.get(
    "/{alert_id}", response_model=AlertOut, dependencies=[Depends(require("alerts.read", "alert"))]
)
async def get_alert(
    alert_id: uuid.UUID, ctx: Context, session: TenantSession, publisher: Publisher
) -> AlertOut:
    obj = await AlertService(session, ctx, publisher).get(alert_id)
    return AlertOut.model_validate(obj)


@router.patch(
    "/{alert_id}",
    response_model=AlertOut,
    dependencies=[Depends(require("alerts.update", "alert"))],
)
async def update_alert(
    alert_id: uuid.UUID,
    data: AlertUpdate,
    ctx: Context,
    session: TenantSession,
    publisher: Publisher,
) -> AlertOut:
    obj = await AlertService(session, ctx, publisher).update(alert_id, data)
    return AlertOut.model_validate(obj)


@router.delete(
    "/{alert_id}", status_code=204, dependencies=[Depends(require("alerts.delete", "alert"))]
)
async def delete_alert(
    alert_id: uuid.UUID, ctx: Context, session: TenantSession, publisher: Publisher
) -> None:
    await AlertService(session, ctx, publisher).delete(alert_id)
