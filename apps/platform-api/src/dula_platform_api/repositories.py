"""Tenant-scoped repositories (ports & adapters — ServiceArchitecture.md §2).

Every read and write is filtered by ``tenant_id`` and excludes soft-deleted rows. This
is the primary, deterministically-testable tenant-isolation guarantee; DB row-level
security (ADR-0006) is defence-in-depth on top of it.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from dula_platform_api.models import Alert, Asset, Incident, TenantEntity


class TenantRepository[ModelT: TenantEntity]:
    """Generic CRUD scoped to a single tenant."""

    model: type[ModelT]

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id

    async def create(self, **values: Any) -> ModelT:
        obj = self.model(tenant_id=self._tenant_id, **values)
        self._session.add(obj)
        await self._session.flush()
        await self._session.refresh(obj)
        return obj

    async def get(self, entity_id: uuid.UUID) -> ModelT | None:
        stmt = select(self.model).where(
            self.model.id == entity_id,
            self.model.tenant_id == self._tenant_id,
            self.model.deleted_at.is_(None),
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def list(self, *, limit: int = 50, offset: int = 0) -> tuple[list[ModelT], int]:
        base = (
            self.model.tenant_id == self._tenant_id,
            self.model.deleted_at.is_(None),
        )
        rows = (
            (
                await self._session.execute(
                    select(self.model)
                    .where(*base)
                    .order_by(self.model.created_at.desc())
                    .limit(limit)
                    .offset(offset)
                )
            )
            .scalars()
            .all()
        )
        total = (
            await self._session.execute(select(func.count()).select_from(self.model).where(*base))
        ).scalar_one()
        return list(rows), total

    async def update(self, obj: ModelT, values: dict[str, Any]) -> ModelT:
        for key, value in values.items():
            setattr(obj, key, value)
        await self._session.flush()
        await self._session.refresh(obj)
        return obj

    async def soft_delete(self, obj: ModelT) -> None:
        obj.deleted_at = func.now()
        await self._session.flush()


class AssetRepository(TenantRepository[Asset]):
    model = Asset


class IncidentRepository(TenantRepository[Incident]):
    model = Incident


class AlertRepository(TenantRepository[Alert]):
    model = Alert
