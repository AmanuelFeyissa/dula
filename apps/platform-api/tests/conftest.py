"""Shared test fixtures for the platform API."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from dula_platform_api.config import Settings
from dula_platform_api.main import create_app
from fastapi.testclient import TestClient


@pytest.fixture
def client() -> Iterator[TestClient]:
    # A test-only DB URL; the engine is created lazily and never connected in these tests
    # (health/me do not touch the DB; readiness is covered by integration tests).
    settings = Settings(database_url="postgresql+asyncpg://test:test@localhost:5432/test")
    app = create_app(settings)
    with TestClient(app) as test_client:
        yield test_client
