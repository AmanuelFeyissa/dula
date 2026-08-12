"""OIDC access-token verification (docs/12-API/Authentication.md, ADR-0009).

Verifies Keycloak-issued RS256 JWTs against the realm JWKS, checking signature,
issuer, audience, and expiry. All model output/untrusted input elsewhere is untrusted;
here we establish *authenticated* identity only — authorization is enforced separately
(OPA, docs/12-API/Authorization.md).
"""

from __future__ import annotations

from typing import Any

import jwt
from jwt import PyJWKClient
from pydantic import BaseModel, Field


class AuthError(Exception):
    """Raised when a token cannot be verified."""


class TokenClaims(BaseModel):
    """The subset of verified claims Dula relies on."""

    subject: str = Field(alias="sub")
    username: str | None = Field(default=None, alias="preferred_username")
    email: str | None = None
    tenant_id: str | None = None
    roles: list[str] = Field(default_factory=list)
    issuer: str = Field(alias="iss")

    model_config = {"populate_by_name": True}


class OIDCVerifier:
    """Verifies bearer tokens for a single OIDC issuer/audience.

    `issuer` is the realm URL (e.g. http://localhost:8080/realms/dula); the JWKS is
    fetched from the standard `{issuer}/protocol/openid-connect/certs` endpoint and
    cached by PyJWKClient.
    """

    def __init__(self, issuer: str, audience: str, *, jwks_uri: str | None = None) -> None:
        self._issuer = issuer.rstrip("/")
        self._audience = audience
        uri = jwks_uri or f"{self._issuer}/protocol/openid-connect/certs"
        self._jwks_client = PyJWKClient(uri)

    def verify(self, token: str) -> TokenClaims:
        """Verify a raw bearer token and return its claims, or raise AuthError."""
        try:
            signing_key = self._jwks_client.get_signing_key_from_jwt(token)
            decoded: dict[str, Any] = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=self._audience,
                issuer=self._issuer,
                options={"require": ["exp", "iss", "sub"]},
            )
        except (jwt.PyJWTError, jwt.PyJWKClientError) as exc:
            raise AuthError(str(exc)) from exc
        return self._to_claims(decoded)

    @staticmethod
    def _to_claims(decoded: dict[str, Any]) -> TokenClaims:
        realm_access = decoded.get("realm_access") or {}
        roles = realm_access.get("roles", []) if isinstance(realm_access, dict) else []
        return TokenClaims(
            sub=decoded["sub"],
            preferred_username=decoded.get("preferred_username"),
            email=decoded.get("email"),
            tenant_id=decoded.get("tenant_id"),
            roles=list(roles),
            iss=decoded["iss"],
        )
