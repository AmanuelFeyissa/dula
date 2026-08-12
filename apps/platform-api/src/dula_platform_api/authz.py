"""Service-layer authorization via OPA (ADR-0009, docs/12-API/Authorization.md).

``require(action, resource_type)`` returns a FastAPI dependency that asks OPA whether the
caller's roles permit ``action`` within their tenant. Decisions fail closed (OPA outage =>
deny) and every **deny** is audited. Cross-tenant object access is additionally prevented by
the tenant-scoped repositories (defence-in-depth).
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Annotated

from dula_common.opa import OPAClient
from fastapi import Depends, HTTPException, Request, status

from dula_platform_api.audit import record_audit
from dula_platform_api.db import TenantSession
from dula_platform_api.deps import Context, RequestContext


def get_opa(request: Request) -> OPAClient:
    opa: OPAClient = request.app.state.opa
    return opa


OPADep = Annotated[OPAClient, Depends(get_opa)]


def require(action: str, resource_type: str) -> Callable[..., Awaitable[None]]:
    """Build a dependency enforcing ``action`` on ``resource_type`` for the caller."""

    async def _enforce(
        ctx: Context,
        session: TenantSession,
        opa: OPADep,
    ) -> None:
        input_doc = {
            "subject": {"roles": list(ctx.roles), "tenant_id": str(ctx.tenant_id)},
            "action": action,
            "resource": {"tenant_id": str(ctx.tenant_id)},
        }
        if await opa.allow(input_doc):
            return
        await _audit_deny(session, ctx, action=action, resource_type=resource_type)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Not authorized for action '{action}'",
        )

    return _enforce


async def _audit_deny(
    session: TenantSession, ctx: RequestContext, *, action: str, resource_type: str
) -> None:
    await record_audit(session, ctx, action=action, resource_type=resource_type, decision="deny")
    await session.commit()
