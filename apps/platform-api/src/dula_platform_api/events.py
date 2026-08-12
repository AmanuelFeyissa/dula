"""Domain-event helpers for the Platform API (DataArchitecture.md §2).

Thin wrapper over the shared ``EventPublisher`` that stamps the tenant and shape of each
event. Publishing is best-effort (the publisher degrades gracefully when the bus is down).
"""

from __future__ import annotations

import uuid
from typing import Annotated, Any

from dula_common.events import EventEnvelope, EventPublisher
from fastapi import Depends, Request

from dula_platform_api.deps import RequestContext

# Domain events emitted in Phase 02 (``domain.entity.action`` — NamingConventions.md).
ASSET_CREATED = "asset.created"
ASSET_UPDATED = "asset.updated"
ASSET_DELETED = "asset.deleted"
INCIDENT_CREATED = "incident.created"
INCIDENT_UPDATED = "incident.updated"
INCIDENT_DELETED = "incident.deleted"
ALERT_CREATED = "alert.created"
ALERT_UPDATED = "alert.updated"
ALERT_DELETED = "alert.deleted"


def get_publisher(request: Request) -> EventPublisher:
    publisher: EventPublisher = request.app.state.publisher
    return publisher


Publisher = Annotated[EventPublisher, Depends(get_publisher)]


async def emit(
    publisher: EventPublisher,
    ctx: RequestContext,
    event_type: str,
    resource_id: uuid.UUID,
    data: dict[str, Any] | None = None,
) -> None:
    envelope = EventEnvelope(
        type=event_type,
        tenant_id=str(ctx.tenant_id),
        data={"id": str(resource_id), "actor": ctx.subject, **(data or {})},
    )
    await publisher.publish(envelope)
