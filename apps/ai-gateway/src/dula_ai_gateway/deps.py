"""Auth + authorization dependencies for the AI Gateway (ADR-0009).

Authenticates the bearer token (OIDC) into a tenant-scoped context and enforces per-action
authorization via OPA (fail-closed). Mirrors the platform-api pattern; the AI Gateway holds
no database, so authorization denials are audited via logs/events rather than a DB row.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from functools import lru_cache
from typing import Annotated

from dula_ai.factory import RagStack
from dula_common.auth import AuthError, OIDCVerifier, TokenClaims
from dula_common.opa import OPAClient
from fastapi import Depends, Header, HTTPException, Request, status

from dula_ai_gateway.config import Settings, get_settings

_log = logging.getLogger(__name__)


@lru_cache
def _verifier(issuer: str, audience: str) -> OIDCVerifier:
    return OIDCVerifier(issuer, audience)


def get_verifier(settings: Annotated[Settings, Depends(get_settings)]) -> OIDCVerifier:
    return _verifier(settings.issuer, settings.api_audience)


def get_current_user(
    verifier: Annotated[OIDCVerifier, Depends(get_verifier)],
    authorization: Annotated[str | None, Header()] = None,
) -> TokenClaims:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        return verifier.verify(authorization.split(" ", 1)[1].strip())
    except AuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


@dataclass(frozen=True, slots=True)
class RequestContext:
    subject: str
    tenant: str
    roles: tuple[str, ...]


def get_request_context(
    user: Annotated[TokenClaims, Depends(get_current_user)],
) -> RequestContext:
    if not user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Token is missing a tenant_id claim"
        )
    return RequestContext(subject=user.subject, tenant=user.tenant_id, roles=tuple(user.roles))


Context = Annotated[RequestContext, Depends(get_request_context)]


def get_opa(request: Request) -> OPAClient:
    opa: OPAClient = request.app.state.opa
    return opa


OPADep = Annotated[OPAClient, Depends(get_opa)]


def get_subsystem(request: Request) -> RagStack:
    subsystem: RagStack = request.app.state.subsystem
    return subsystem


Subsystem = Annotated[RagStack, Depends(get_subsystem)]


def require(action: str) -> Callable[..., Awaitable[None]]:
    """Build a dependency enforcing ``action`` for the caller (fail-closed, audited)."""

    async def _enforce(ctx: Context, opa: OPADep) -> None:
        allowed = await opa.allow(
            {
                "subject": {"roles": list(ctx.roles), "tenant_id": ctx.tenant},
                "action": action,
                "resource": {"tenant_id": ctx.tenant},
            }
        )
        if not allowed:
            _log.warning(
                "authorization denied",
                extra={"subject": ctx.subject, "tenant": ctx.tenant, "action": action},
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not authorized for action '{action}'",
            )

    return _enforce
