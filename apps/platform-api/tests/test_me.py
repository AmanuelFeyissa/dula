"""/api/v1/me auth behavior: 401 without a token, 200 with verified claims."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from dula_common.auth import TokenClaims
from dula_platform_api.config import Settings
from dula_platform_api.deps import get_current_user
from dula_platform_api.main import create_app
from fastapi.testclient import TestClient


def test_me_requires_bearer_token(client: TestClient) -> None:
    resp = client.get("/api/v1/me")
    assert resp.status_code == 401


@pytest.fixture
def authed_client() -> Iterator[TestClient]:
    settings = Settings(database_url="postgresql+asyncpg://test:test@localhost:5432/test")
    app = create_app(settings)

    def fake_user() -> TokenClaims:
        return TokenClaims(
            sub="user-123",
            preferred_username="maya",
            email="maya@example.test",
            tenant_id="tenant-a",
            roles=["analyst"],
            iss=settings.issuer,
        )

    app.dependency_overrides[get_current_user] = fake_user
    with TestClient(app) as test_client:
        yield test_client


def test_me_returns_claims(authed_client: TestClient) -> None:
    resp = authed_client.get("/api/v1/me")
    assert resp.status_code == 200
    body = resp.json()
    assert body["subject"] == "user-123"
    assert body["username"] == "maya"
    assert body["tenant_id"] == "tenant-a"
    assert body["roles"] == ["analyst"]
