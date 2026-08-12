"""Asset endpoints (docs/12-API/APIStandards.md). AuthZ via OPA; tenant-scoped."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from dula_platform_api.authz import require
from dula_platform_api.db import TenantSession
from dula_platform_api.deps import Context
from dula_platform_api.events import Publisher
from dula_platform_api.schemas import AssetCreate, AssetOut, AssetUpdate, Page
from dula_platform_api.services import AssetService

router = APIRouter(prefix="/api/v1/assets", tags=["assets"])


@router.post(
    "",
    response_model=AssetOut,
    status_code=201,
    dependencies=[Depends(require("assets.create", "asset"))],
)
async def create_asset(
    data: AssetCreate, ctx: Context, session: TenantSession, publisher: Publisher
) -> AssetOut:
    obj = await AssetService(session, ctx, publisher).create(data)
    return AssetOut.model_validate(obj)


@router.get(
    "", response_model=Page[AssetOut], dependencies=[Depends(require("assets.read", "asset"))]
)
async def list_assets(
    ctx: Context,
    session: TenantSession,
    publisher: Publisher,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Page[AssetOut]:
    items, total = await AssetService(session, ctx, publisher).list(limit=limit, offset=offset)
    return Page[AssetOut](
        items=[AssetOut.model_validate(a) for a in items], total=total, limit=limit, offset=offset
    )


@router.get(
    "/{asset_id}", response_model=AssetOut, dependencies=[Depends(require("assets.read", "asset"))]
)
async def get_asset(
    asset_id: uuid.UUID, ctx: Context, session: TenantSession, publisher: Publisher
) -> AssetOut:
    obj = await AssetService(session, ctx, publisher).get(asset_id)
    return AssetOut.model_validate(obj)


@router.patch(
    "/{asset_id}",
    response_model=AssetOut,
    dependencies=[Depends(require("assets.update", "asset"))],
)
async def update_asset(
    asset_id: uuid.UUID,
    data: AssetUpdate,
    ctx: Context,
    session: TenantSession,
    publisher: Publisher,
) -> AssetOut:
    obj = await AssetService(session, ctx, publisher).update(asset_id, data)
    return AssetOut.model_validate(obj)


@router.delete(
    "/{asset_id}", status_code=204, dependencies=[Depends(require("assets.delete", "asset"))]
)
async def delete_asset(
    asset_id: uuid.UUID, ctx: Context, session: TenantSession, publisher: Publisher
) -> None:
    await AssetService(session, ctx, publisher).delete(asset_id)
