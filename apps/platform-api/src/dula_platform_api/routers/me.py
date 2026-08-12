"""Current-user endpoint — proves the end-to-end OIDC login path (UC-10)."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from dula_platform_api.deps import CurrentUser

router = APIRouter(prefix="/api/v1", tags=["identity"])


class MeResponse(BaseModel):
    subject: str
    username: str | None
    email: str | None
    tenant_id: str | None
    roles: list[str]


@router.get("/me", response_model=MeResponse)
async def me(user: CurrentUser) -> MeResponse:
    return MeResponse(
        subject=user.subject,
        username=user.username,
        email=user.email,
        tenant_id=user.tenant_id,
        roles=user.roles,
    )
