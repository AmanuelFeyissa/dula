"""Tests for OIDC token verification using a locally generated RSA key.

We avoid any network/Keycloak dependency by stubbing the JWKS lookup and signing tokens
with a test key. This exercises signature, issuer, audience, and expiry checks.
"""

from __future__ import annotations

import datetime as dt
from typing import Any

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from dula_common.auth import AuthError, OIDCVerifier

ISSUER = "http://localhost:8080/realms/dula"
AUDIENCE = "dula-api"


class _FakeSigningKey:
    def __init__(self, key: Any) -> None:
        self.key = key


@pytest.fixture(scope="module")
def keypair() -> tuple[bytes, Any]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    return private_pem, private_key.public_key()


def _make_token(private_pem: bytes, **overrides: Any) -> str:
    now = dt.datetime.now(tz=dt.UTC)
    payload: dict[str, Any] = {
        "sub": "user-123",
        "preferred_username": "maya",
        "email": "maya@example.test",
        "tenant_id": "tenant-a",
        "realm_access": {"roles": ["analyst"]},
        "iss": ISSUER,
        "aud": AUDIENCE,
        "iat": now,
        "exp": now + dt.timedelta(minutes=5),
    }
    payload.update(overrides)
    return jwt.encode(payload, private_pem, algorithm="RS256")


def _verifier(public_key: Any, monkeypatch: pytest.MonkeyPatch) -> OIDCVerifier:
    verifier = OIDCVerifier(ISSUER, AUDIENCE)
    monkeypatch.setattr(
        verifier._jwks_client,
        "get_signing_key_from_jwt",
        lambda _token: _FakeSigningKey(public_key),
    )
    return verifier


def test_valid_token_returns_claims(
    keypair: tuple[bytes, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    private_pem, public_key = keypair
    verifier = _verifier(public_key, monkeypatch)
    claims = verifier.verify(_make_token(private_pem))
    assert claims.subject == "user-123"
    assert claims.username == "maya"
    assert claims.tenant_id == "tenant-a"
    assert "analyst" in claims.roles
    assert claims.issuer == ISSUER


def test_wrong_audience_rejected(
    keypair: tuple[bytes, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    private_pem, public_key = keypair
    verifier = _verifier(public_key, monkeypatch)
    with pytest.raises(AuthError):
        verifier.verify(_make_token(private_pem, aud="someone-else"))


def test_expired_token_rejected(
    keypair: tuple[bytes, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    private_pem, public_key = keypair
    verifier = _verifier(public_key, monkeypatch)
    past = dt.datetime.now(tz=dt.UTC) - dt.timedelta(minutes=10)
    with pytest.raises(AuthError):
        verifier.verify(_make_token(private_pem, exp=past))
