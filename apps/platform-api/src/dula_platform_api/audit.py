"""Audit logging of data access and authorization decisions (DataSecurity.md).

Writes append-only ``audit_events`` rows within the caller's tenant session. The caller
controls the transaction boundary (commit); this helper only stages the row.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from dula_platform_api.deps import RequestContext
from dula_platform_api.models import AuditEvent


async def record_audit(
    session: AsyncSession,
    ctx: RequestContext,
    *,
    action: str,
    resource_type: str,
    decision: str,
    resource_id: uuid.UUID | str | None = None,
    detail: dict[str, Any] | None = None,
) -> None:
    session.add(
        AuditEvent(
            tenant_id=ctx.tenant_id,
            actor_subject=ctx.subject,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id is not None else None,
            decision=decision,
            detail=detail or {},
        )
    )
    await session.flush()
