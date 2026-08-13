"""Plugin/connector endpoints (Phase 07): list plugins, enable/disable, invoke read connectors.

Listing and read-connector invocation are available to operational personas; enable/disable is
admin-only. **Consequential** connector capabilities are *not* invokable directly here — they must
run through an agent so they are human-approval-gated. Per-capability authorization is enforced by
the plugin host (OPA); this router adds the coarse endpoint gate and the read-only restriction.
"""

from __future__ import annotations

from typing import Any

from dula_plugins.host import HostError
from dula_plugins.manifest import SideEffect
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from dula_ai_gateway.deps import Context, Plugins, require

router = APIRouter(prefix="/api/v1", tags=["plugins"])


class CapabilityOut(BaseModel):
    name: str
    side_effect: str
    permission: str
    requires_egress: bool


class PluginOut(BaseModel):
    id: str
    version: str
    description: str
    state: str
    capabilities: list[CapabilityOut]


class InvokeRequest(BaseModel):
    args: dict[str, Any] = Field(default_factory=dict)


class InvokeResponse(BaseModel):
    ok: bool
    output: Any
    error: str | None
    untrusted: bool


@router.get(
    "/plugins", response_model=list[PluginOut], dependencies=[Depends(require("plugins.read"))]
)
async def list_plugins(ctx: Context, plugins: Plugins) -> list[PluginOut]:
    out: list[PluginOut] = []
    for p in plugins.host.installed():
        m = p.manifest
        out.append(
            PluginOut(
                id=m.id,
                version=m.version,
                description=m.description,
                state=p.state.value,
                capabilities=[
                    CapabilityOut(
                        name=c.name,
                        side_effect=c.side_effect.value,
                        permission=c.permission,
                        requires_egress=c.requires_egress,
                    )
                    for c in m.capabilities
                ],
            )
        )
    return out


def _set_state(plugins: Plugins, plugin_id: str, *, enable: bool) -> None:
    try:
        if enable:
            plugins.host.enable(plugin_id)
        else:
            plugins.host.disable(plugin_id)
    except HostError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post(
    "/plugins/{plugin_id}/enable",
    status_code=204,
    dependencies=[Depends(require("plugins.admin"))],
)
async def enable_plugin(plugin_id: str, ctx: Context, plugins: Plugins) -> None:
    _set_state(plugins, plugin_id, enable=True)


@router.post(
    "/plugins/{plugin_id}/disable",
    status_code=204,
    dependencies=[Depends(require("plugins.admin"))],
)
async def disable_plugin(plugin_id: str, ctx: Context, plugins: Plugins) -> None:
    _set_state(plugins, plugin_id, enable=False)


@router.post(
    "/connectors/{capability}/invoke",
    response_model=InvokeResponse,
    dependencies=[Depends(require("connectors.invoke"))],
)
async def invoke_connector(
    capability: str, data: InvokeRequest, ctx: Context, plugins: Plugins
) -> InvokeResponse:
    found = plugins.host.find_capability(capability)
    if found is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="unknown capability")
    _plugin, cap = found
    if cap.side_effect is SideEffect.CONSEQUENTIAL:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="consequential capabilities must run through an agent (human approval required)",
        )
    try:
        result = await plugins.host.invoke(
            capability, data.args, tenant=ctx.tenant, subject=ctx.subject, roles=list(ctx.roles)
        )
    except HostError as exc:
        # Authorization failures surface as 403; other host errors as 400.
        code = (
            status.HTTP_403_FORBIDDEN
            if "not authorized" in str(exc)
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(status_code=code, detail=str(exc)) from exc
    return InvokeResponse(
        ok=result.ok, output=result.output, error=result.error, untrusted=result.untrusted
    )
