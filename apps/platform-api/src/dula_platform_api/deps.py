"""Auth dependencies: authenticate the bearer token into TokenClaims (ADR-0009).

Authorization (RBAC/ABAC via OPA) is enforced separately — see
docs/12-API/Authorization.md.
"""

from __future__ import annotations

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
