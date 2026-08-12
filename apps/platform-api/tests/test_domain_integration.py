"""Integration tests against a real Postgres: tenant isolation + service-layer authZ.

These exercise the full request path (router -> authz -> service -> tenant repository ->
DB). They are skipped automatically when no Postgres is reachable (e.g. the CI unit lane);
run the dev stack (`make up`) and `alembic upgrade head`, or point
``DULA_TEST_DATABASE_URL`` at a database, to run them.

The proven guarantee here is **application-level tenant scoping**: tenant B can never read,
update, or delete tenant A's rows. DB row-level security (ADR-0006) is verified separately
against the migrated schema (see the milestone closure report).
"""

from __future__ import annotations

import asyncio
import os
import uuid
from collections.abc import Iterator
from typing import Any

import pytest
from dula_platform_api.config import Settings
from dula_platform_api.deps import RequestContext, get_request_context
from dula_platform_api.main import create_app
from dula_platform_api.models import Base, Tenant
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

TEST_DB_URL = os.environ.get(
    "DULA_TEST_DATABASE_URL",
    "postgresql+asyncpg://dula:dula_dev_password@localhost:5432/dula",
)
TENANT_A = uuid.UUID("11111111-1111-1111-1111-111111111111")
TENANT_B = uuid.UUID("22222222-2222-2222-2222-222222222222")


class _StubOPA:
    """Deterministic OPA stand-in so tests assert the enforcement wiring, not policy I/O."""

    def __init__(self, allow: bool = True) -> None:
        self.allow_result = allow

    async def allow(self, _input: dict[str, Any]) -> bool:
        return self.allow_result


async def _prepare_schema() -> None:
    engine = create_async_engine(TEST_DB_URL)
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        maker = async_sessionmaker(engine, expire_on_commit=False)
        async with maker() as session:
            session.add_all([Tenant(id=TENANT_A, name="tenant-a"), Tenant(id=TENANT_B, name="t-b")])
            await session.commit()
    finally:
        await engine.dispose()


@pytest.fixture(scope="module")
def _schema() -> Iterator[None]:
    try:
        asyncio.run(_prepare_schema())
    except Exception as exc:
        pytest.skip(f"Postgres not available for integration tests: {exc}")
    yield


@pytest.fixture
def env(_schema: None) -> Iterator[tuple[TestClient, dict[str, RequestContext], _StubOPA]]:
    """A TestClient with swappable caller context and a stub OPA."""
    settings = Settings(database_url=TEST_DB_URL, events_enabled=False)
    app = create_app(settings)
    holder: dict[str, RequestContext] = {
        "ctx": RequestContext(
            subject="user-a", tenant_id=TENANT_A, roles=("admin",), username="a", email=None
        )
    }
    app.dependency_overrides[get_request_context] = lambda: holder["ctx"]
    with TestClient(app) as client:
        opa = _StubOPA(allow=True)
        client.app.state.opa = opa  # type: ignore[attr-defined]
        yield client, holder, opa


def _as(holder: dict[str, RequestContext], tenant: uuid.UUID, *roles: str) -> None:
    holder["ctx"] = RequestContext(
        subject=f"user-{tenant}", tenant_id=tenant, roles=roles, username="u", email=None
    )


def test_create_and_read_within_tenant(
    env: tuple[TestClient, dict[str, RequestContext], _StubOPA],
) -> None:
    client, holder, _ = env
    _as(holder, TENANT_A, "admin")
    created = client.post("/api/v1/alerts", json={"title": "brute force", "severity": "high"})
    assert created.status_code == 201, created.text
    alert_id = created.json()["id"]

    got = client.get(f"/api/v1/alerts/{alert_id}")
    assert got.status_code == 200
    assert got.json()["title"] == "brute force"
    assert got.json()["tenant_id"] == str(TENANT_A)


def test_cross_tenant_read_is_blocked(
    env: tuple[TestClient, dict[str, RequestContext], _StubOPA],
) -> None:
    client, holder, _ = env
    _as(holder, TENANT_A, "admin")
    alert_id = client.post("/api/v1/alerts", json={"title": "secret-a"}).json()["id"]

    # Tenant B must not see tenant A's alert — 404, and never in the list.
    _as(holder, TENANT_B, "admin")
    assert client.get(f"/api/v1/alerts/{alert_id}").status_code == 404
    listing = client.get("/api/v1/alerts").json()
    assert all(item["id"] != alert_id for item in listing["items"])


def test_cross_tenant_update_and_delete_blocked(
    env: tuple[TestClient, dict[str, RequestContext], _StubOPA],
) -> None:
    client, holder, _ = env
    _as(holder, TENANT_A, "admin")
    alert_id = client.post("/api/v1/alerts", json={"title": "owned-by-a"}).json()["id"]

    _as(holder, TENANT_B, "admin")
    assert client.patch(f"/api/v1/alerts/{alert_id}", json={"title": "hijack"}).status_code == 404
    assert client.delete(f"/api/v1/alerts/{alert_id}").status_code == 404

    # The row is untouched for its owner.
    _as(holder, TENANT_A, "admin")
    assert client.get(f"/api/v1/alerts/{alert_id}").json()["title"] == "owned-by-a"


def test_authz_denies_when_opa_denies(
    env: tuple[TestClient, dict[str, RequestContext], _StubOPA],
) -> None:
    client, holder, opa = env
    _as(holder, TENANT_A, "analyst")
    opa.allow_result = False
    resp = client.post("/api/v1/alerts", json={"title": "should-be-denied"})
    assert resp.status_code == 403


def test_soft_delete_hides_row(
    env: tuple[TestClient, dict[str, RequestContext], _StubOPA],
) -> None:
    client, holder, _ = env
    _as(holder, TENANT_A, "admin")
    alert_id = client.post("/api/v1/alerts", json={"title": "temp"}).json()["id"]
    assert client.delete(f"/api/v1/alerts/{alert_id}").status_code == 204
    assert client.get(f"/api/v1/alerts/{alert_id}").status_code == 404
