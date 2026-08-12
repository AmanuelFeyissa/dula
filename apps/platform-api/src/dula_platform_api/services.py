"""Application services (use cases) for the domain spine — ServiceArchitecture.md §1-2.

Each method owns a unit of work: mutate via the tenant-scoped repository, write an audit
record, commit, then best-effort publish a domain event. Route handlers stay thin and call
these; business rules and cross-cutting concerns (audit, events) live here.
"""

from __future__ import annotations

import uuid

from dula_common.events import EventPublisher
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from dula_platform_api import events
from dula_platform_api.audit import record_audit
from dula_platform_api.deps import RequestContext
from dula_platform_api.models import Alert, Asset, Incident, TenantEntity
from dula_platform_api.repositories import (
    AlertRepository,
    AssetRepository,
    IncidentRepository,
    TenantRepository,
)
from dula_platform_api.schemas import (
    AlertCreate,
    AlertUpdate,
    AssetCreate,
    AssetUpdate,
    IncidentCreate,
    IncidentUpdate,
)


class BaseService[ModelT: TenantEntity]:
    resource_type: str
    event_created: str
    event_updated: str
    event_deleted: str

    def __init__(
        self,
        session: AsyncSession,
        ctx: RequestContext,
        repo: TenantRepository[ModelT],
        publisher: EventPublisher,
    ) -> None:
        self._session = session
        self._ctx = ctx
        self._repo = repo
        self._publisher = publisher

    async def get(self, entity_id: uuid.UUID) -> ModelT:
        obj = await self._repo.get(entity_id)
        if obj is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"{self.resource_type} not found"
            )
        return obj

    async def list(self, *, limit: int, offset: int) -> tuple[list[ModelT], int]:
        return await self._repo.list(limit=limit, offset=offset)

    async def delete(self, entity_id: uuid.UUID) -> None:
        obj = await self.get(entity_id)
        await self._repo.soft_delete(obj)
        await self._audit(f"{self.resource_type}s.delete", obj.id)
        await self._session.commit()
        await events.emit(self._publisher, self._ctx, self.event_deleted, obj.id)

    async def _audit(self, action: str, resource_id: uuid.UUID) -> None:
        await record_audit(
            self._session,
            self._ctx,
            action=action,
            resource_type=self.resource_type,
            resource_id=resource_id,
            decision="allow",
        )


class AssetService(BaseService[Asset]):
    resource_type = "asset"
    event_created = events.ASSET_CREATED
    event_updated = events.ASSET_UPDATED
    event_deleted = events.ASSET_DELETED

    def __init__(
        self, session: AsyncSession, ctx: RequestContext, publisher: EventPublisher
    ) -> None:
        super().__init__(session, ctx, AssetRepository(session, ctx.tenant_id), publisher)

    async def create(self, data: AssetCreate) -> Asset:
        obj = await self._repo.create(**data.model_dump())
        await self._audit("assets.create", obj.id)
        await self._session.commit()
        await events.emit(self._publisher, self._ctx, self.event_created, obj.id)
        return obj

    async def update(self, entity_id: uuid.UUID, data: AssetUpdate) -> Asset:
        obj = await self.get(entity_id)
        obj = await self._repo.update(obj, data.model_dump(exclude_unset=True))
        await self._audit("assets.update", obj.id)
        await self._session.commit()
        await events.emit(self._publisher, self._ctx, self.event_updated, obj.id)
        return obj


class IncidentService(BaseService[Incident]):
    resource_type = "incident"
    event_created = events.INCIDENT_CREATED
    event_updated = events.INCIDENT_UPDATED
    event_deleted = events.INCIDENT_DELETED

    def __init__(
        self, session: AsyncSession, ctx: RequestContext, publisher: EventPublisher
    ) -> None:
        super().__init__(session, ctx, IncidentRepository(session, ctx.tenant_id), publisher)

    async def create(self, data: IncidentCreate) -> Incident:
        obj = await self._repo.create(**data.model_dump())
        await self._audit("incidents.create", obj.id)
        await self._session.commit()
        await events.emit(self._publisher, self._ctx, self.event_created, obj.id)
        return obj

    async def update(self, entity_id: uuid.UUID, data: IncidentUpdate) -> Incident:
        obj = await self.get(entity_id)
        obj = await self._repo.update(obj, data.model_dump(exclude_unset=True))
        await self._audit("incidents.update", obj.id)
        await self._session.commit()
        await events.emit(self._publisher, self._ctx, self.event_updated, obj.id)
        return obj


class AlertService(BaseService[Alert]):
    resource_type = "alert"
    event_created = events.ALERT_CREATED
    event_updated = events.ALERT_UPDATED
    event_deleted = events.ALERT_DELETED

    def __init__(
        self, session: AsyncSession, ctx: RequestContext, publisher: EventPublisher
    ) -> None:
        super().__init__(session, ctx, AlertRepository(session, ctx.tenant_id), publisher)

    async def create(self, data: AlertCreate) -> Alert:
        await self._validate_links(data.asset_id, data.incident_id)
        obj = await self._repo.create(**data.model_dump())
        await self._audit("alerts.create", obj.id)
        await self._session.commit()
        await events.emit(self._publisher, self._ctx, self.event_created, obj.id)
        return obj

    async def update(self, entity_id: uuid.UUID, data: AlertUpdate) -> Alert:
        obj = await self.get(entity_id)
        values = data.model_dump(exclude_unset=True)
        await self._validate_links(values.get("asset_id"), values.get("incident_id"))
        obj = await self._repo.update(obj, values)
        await self._audit("alerts.update", obj.id)
        await self._session.commit()
        await events.emit(self._publisher, self._ctx, self.event_updated, obj.id)
        return obj

    async def _validate_links(
        self, asset_id: uuid.UUID | None, incident_id: uuid.UUID | None
    ) -> None:
        """Reject links to assets/incidents outside the caller's tenant (404, not leak)."""
        if asset_id is not None:
            found = await AssetRepository(self._session, self._ctx.tenant_id).get(asset_id)
            if found is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="asset not found")
        if incident_id is not None:
            found_inc = await IncidentRepository(self._session, self._ctx.tenant_id).get(
                incident_id
            )
            if found_inc is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="incident not found"
                )
