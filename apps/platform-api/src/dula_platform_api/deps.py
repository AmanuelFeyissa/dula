"""Auth dependencies: authenticate the bearer token into TokenClaims (ADR-0009).

Authorization (RBAC/ABAC via OPA) is enforced separately — see
docs/12-API/Authorization.md and ``authz.py``.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from functools import lru_cache
from typing import Annotated

from dula_common.auth import AuthError, OIDCVerifier, TokenClaims
from fastapi import Depends, Header, HTTPException, status

from dula_platform_api.config import Settings, get_settings


@lru_cache
def _verifier(issuer: str, audience: str) -> OIDCVerifier:
    return OIDCVerifier(issuer, audience)


def get_verifier(settings: Annotated[Settings, Depends(get_settings)]) -> OIDCVerifier:
    return _verifier(settings.issuer, settings.api_audience)


def get_current_user(
    verifier: Annotated[OIDCVerifier, Depends(get_verifier)],
    authorization: Annotated[str | None, Header()] = None,
) -> TokenClaims:
    """Verify the `Authorization: Bearer <token>` header, returning claims or 401."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = authorization.split(" ", 1)[1].strip()
    try:
        return verifier.verify(token)
    except AuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


CurrentUser = Annotated[TokenClaims, Depends(get_current_user)]


@dataclass(frozen=True, slots=True)
class RequestContext:
    """The verified caller reduced to what the domain layer needs.

    ``tenant_id`` is derived from the signed ``tenant_id`` claim and is the single
    tenant scope applied to every query and to the RLS session variable.
    """

    subject: str
    tenant_id: uuid.UUID
    roles: tuple[str, ...]
    username: str | None
    email: str | None


def get_request_context(user: CurrentUser) -> RequestContext:
    """Build the per-request context, rejecting tokens without a valid tenant."""
    if not user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Token is missing a tenant_id claim"
        )
    try:
        tenant = uuid.UUID(user.tenant_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="tenant_id claim is not a valid UUID"
        ) from exc
    return RequestContext(
        subject=user.subject,
        tenant_id=tenant,
        roles=tuple(user.roles),
        username=user.username,
        email=user.email,
    )


Context = Annotated[RequestContext, Depends(get_request_context)]
