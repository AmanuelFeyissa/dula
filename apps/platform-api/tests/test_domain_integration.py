"""Integration tests against a real Postgres: tenant isolation, service authZ, list queries.

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


async def _create_tenant() -> uuid.UUID:
    tenant_id = uuid.uuid4()
    engine = create_async_engine(TEST_DB_URL)
    try:
        maker = async_sessionmaker(engine, expire_on_commit=False)
        async with maker() as session:
            session.add(Tenant(id=tenant_id, name=f"query-test-{tenant_id}"))
            await session.commit()
    finally:
        await engine.dispose()
    return tenant_id


@pytest.fixture
def fresh_tenant(_schema: None) -> uuid.UUID:
    """A brand-new, single-use tenant.

    The list-query tests below assert exact row counts and exact ordering. TENANT_A/B live
    for the whole module (``_schema`` is module-scoped, with no per-test rollback), so
    reusing either would make one test's seed data silently pollute the next test's counts.
    A fresh tenant per test sidesteps that without needing a transactional-rollback fixture.
    """
    return asyncio.run(_create_tenant())


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


# --- List query contract: filter, search, sort, paginate ------------------------------
#
# Weakness recorded in the M010 plan: the UI had no way to find a specific alert once
# there were more than a handful, and severity ordering was done client-side (correct
# only *within* a page, not across the full list). These tests define the contract
# before repositories.py or the routers implement it.


def _seed_alerts_for_query_tests(client: TestClient) -> None:
    client.post(
        "/api/v1/alerts",
        json={"title": "beacon to evil.example.com", "severity": "critical", "status": "new"},
    )
    client.post(
        "/api/v1/alerts",
        json={"title": "legacy TLS negotiated", "severity": "low", "status": "false_positive"},
    )
    client.post(
        "/api/v1/alerts",
        json={"title": "impossible travel sign-in", "severity": "high", "status": "triaged"},
    )
    client.post(
        "/api/v1/alerts",
        json={"title": "brute force against VPN", "severity": "high", "status": "closed"},
    )
    client.post(
        "/api/v1/alerts",
        json={"title": "anomalous pod exec", "severity": "medium", "status": "new"},
    )


def test_list_alerts_filters_by_severity(
    env: tuple[TestClient, dict[str, RequestContext], _StubOPA],
    fresh_tenant: uuid.UUID,
) -> None:
    client, holder, _ = env
    _as(holder, fresh_tenant, "admin")
    _seed_alerts_for_query_tests(client)

    resp = client.get("/api/v1/alerts", params={"severity": "high"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total"] == 2
    assert {item["title"] for item in body["items"]} == {
        "impossible travel sign-in",
        "brute force against VPN",
    }


def test_list_alerts_filters_by_status(
    env: tuple[TestClient, dict[str, RequestContext], _StubOPA],
    fresh_tenant: uuid.UUID,
) -> None:
    client, holder, _ = env
    _as(holder, fresh_tenant, "admin")
    _seed_alerts_for_query_tests(client)

    resp = client.get("/api/v1/alerts", params={"status": "new"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total"] == 2
    assert {item["title"] for item in body["items"]} == {
        "beacon to evil.example.com",
        "anomalous pod exec",
    }


def test_list_alerts_combines_severity_and_status_filters(
    env: tuple[TestClient, dict[str, RequestContext], _StubOPA],
    fresh_tenant: uuid.UUID,
) -> None:
    client, holder, _ = env
    _as(holder, fresh_tenant, "admin")
    _seed_alerts_for_query_tests(client)

    resp = client.get("/api/v1/alerts", params={"severity": "high", "status": "closed"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["title"] == "brute force against VPN"


def test_list_alerts_searches_title_case_insensitively(
    env: tuple[TestClient, dict[str, RequestContext], _StubOPA],
    fresh_tenant: uuid.UUID,
) -> None:
    client, holder, _ = env
    _as(holder, fresh_tenant, "admin")
    _seed_alerts_for_query_tests(client)

    resp = client.get("/api/v1/alerts", params={"q": "EVIL"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["title"] == "beacon to evil.example.com"


def test_list_alerts_search_matching_nothing_returns_empty(
    env: tuple[TestClient, dict[str, RequestContext], _StubOPA],
    fresh_tenant: uuid.UUID,
) -> None:
    client, holder, _ = env
    _as(holder, fresh_tenant, "admin")
    _seed_alerts_for_query_tests(client)

    resp = client.get("/api/v1/alerts", params={"q": "does-not-exist-anywhere"})
    assert resp.status_code == 200, resp.text
    assert resp.json() == {"items": [], "total": 0, "limit": 50, "offset": 0}


def test_list_alerts_default_order_is_severity_then_recency(
    env: tuple[TestClient, dict[str, RequestContext], _StubOPA],
    fresh_tenant: uuid.UUID,
) -> None:
    """What is on fire belongs at the top — regardless of what page you're looking at.

    This is the behaviour that used to live in the web app's client-side RANK sort
    (apps/web/app/alerts/page.tsx), which only ordered items within a single fetched page.
    Moving it server-side means page 2 is never less urgent-looking than page 1 by accident.
    """
    client, holder, _ = env
    _as(holder, fresh_tenant, "admin")
    _seed_alerts_for_query_tests(client)

    resp = client.get("/api/v1/alerts", params={"limit": 5})
    assert resp.status_code == 200, resp.text
    severities = [item["severity"] for item in resp.json()["items"]]
    rank = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    assert severities == sorted(severities, key=lambda s: rank[s])
    assert severities[0] == "critical"
    assert severities[-1] == "low"


def test_list_alerts_pagination_is_stable_under_severity_order(
    env: tuple[TestClient, dict[str, RequestContext], _StubOPA],
    fresh_tenant: uuid.UUID,
) -> None:
    """Ordering must hold *across* pages, not just within one (the client-side bug)."""
    client, holder, _ = env
    _as(holder, fresh_tenant, "admin")
    _seed_alerts_for_query_tests(client)

    page1 = client.get("/api/v1/alerts", params={"limit": 2, "offset": 0}).json()
    page2 = client.get("/api/v1/alerts", params={"limit": 2, "offset": 2}).json()
    page3 = client.get("/api/v1/alerts", params={"limit": 2, "offset": 4}).json()
    all_items = page1["items"] + page2["items"] + page3["items"]
    assert len(all_items) == 5
    assert len({item["id"] for item in all_items}) == 5  # no duplicates, no gaps

    rank = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    severities = [item["severity"] for item in all_items]
    assert severities == sorted(severities, key=lambda s: rank[s])


def test_list_alerts_sort_title_overrides_the_severity_default(
    env: tuple[TestClient, dict[str, RequestContext], _StubOPA],
    fresh_tenant: uuid.UUID,
) -> None:
    client, holder, _ = env
    _as(holder, fresh_tenant, "admin")
    _seed_alerts_for_query_tests(client)

    resp = client.get("/api/v1/alerts", params={"sort": "title", "limit": 5})
    assert resp.status_code == 200, resp.text
    titles = [item["title"] for item in resp.json()["items"]]
    assert titles == sorted(titles)


def test_list_alerts_sort_accepts_a_descending_prefix(
    env: tuple[TestClient, dict[str, RequestContext], _StubOPA],
    fresh_tenant: uuid.UUID,
) -> None:
    client, holder, _ = env
    _as(holder, fresh_tenant, "admin")
    _seed_alerts_for_query_tests(client)

    resp = client.get("/api/v1/alerts", params={"sort": "-title", "limit": 5})
    assert resp.status_code == 200, resp.text
    titles = [item["title"] for item in resp.json()["items"]]
    assert titles == sorted(titles, reverse=True)


def test_list_alerts_rejects_unknown_sort_field(
    env: tuple[TestClient, dict[str, RequestContext], _StubOPA],
    fresh_tenant: uuid.UUID,
) -> None:
    client, holder, _ = env
    _as(holder, fresh_tenant, "admin")
    resp = client.get("/api/v1/alerts", params={"sort": "description"})
    assert resp.status_code == 422


def test_list_alerts_rejects_unknown_severity(
    env: tuple[TestClient, dict[str, RequestContext], _StubOPA],
    fresh_tenant: uuid.UUID,
) -> None:
    client, holder, _ = env
    _as(holder, fresh_tenant, "admin")
    resp = client.get("/api/v1/alerts", params={"severity": "apocalyptic"})
    assert resp.status_code == 422


def test_list_alerts_filter_cannot_leak_another_tenants_rows(
    env: tuple[TestClient, dict[str, RequestContext], _StubOPA],
    fresh_tenant: uuid.UUID,
) -> None:
    """A filter is still a list query: it must never widen what a tenant can see."""
    client, holder, _ = env
    _as(holder, TENANT_A, "admin")
    client.post("/api/v1/alerts", json={"title": "tenant-a-critical-thing", "severity": "critical"})

    _as(holder, fresh_tenant, "admin")
    _seed_alerts_for_query_tests(client)

    resp = client.get("/api/v1/alerts", params={"severity": "critical"})
    assert resp.status_code == 200, resp.text
    titles = {item["title"] for item in resp.json()["items"]}
    assert "tenant-a-critical-thing" not in titles
    assert titles == {"beacon to evil.example.com"}


# --- Same query contract for incidents and assets --------------------------------------
#
# Not the full alert permutation matrix (that already proves the shared TenantRepository
# machinery works); one filter test, one search test, one default-order test, and one
# rejection test per resource is enough to prove each router actually wires it up.


def test_list_incidents_filters_by_severity_and_status(
    env: tuple[TestClient, dict[str, RequestContext], _StubOPA],
    fresh_tenant: uuid.UUID,
) -> None:
    client, holder, _ = env
    _as(holder, fresh_tenant, "admin")
    client.post("/api/v1/incidents", json={"title": "ransomware precursor", "severity": "critical"})
    client.post(
        "/api/v1/incidents",
        json={"title": "phishing campaign", "severity": "medium", "status": "resolved"},
    )
    client.post("/api/v1/incidents", json={"title": "credential stuffing", "severity": "high"})

    resp = client.get("/api/v1/incidents", params={"severity": "high", "status": "open"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["title"] == "credential stuffing"


def test_list_incidents_searches_title(
    env: tuple[TestClient, dict[str, RequestContext], _StubOPA],
    fresh_tenant: uuid.UUID,
) -> None:
    client, holder, _ = env
    _as(holder, fresh_tenant, "admin")
    client.post("/api/v1/incidents", json={"title": "ransomware precursor activity"})
    client.post("/api/v1/incidents", json={"title": "phishing campaign"})

    resp = client.get("/api/v1/incidents", params={"q": "ransomware"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["total"] == 1


def test_list_incidents_default_order_is_severity_first(
    env: tuple[TestClient, dict[str, RequestContext], _StubOPA],
    fresh_tenant: uuid.UUID,
) -> None:
    client, holder, _ = env
    _as(holder, fresh_tenant, "admin")
    client.post("/api/v1/incidents", json={"title": "low-sev", "severity": "low"})
    client.post("/api/v1/incidents", json={"title": "crit-sev", "severity": "critical"})
    client.post("/api/v1/incidents", json={"title": "med-sev", "severity": "medium"})

    resp = client.get("/api/v1/incidents")
    assert resp.status_code == 200, resp.text
    severities = [item["severity"] for item in resp.json()["items"]]
    assert severities == ["critical", "medium", "low"]


def test_list_incidents_rejects_unknown_status(
    env: tuple[TestClient, dict[str, RequestContext], _StubOPA],
    fresh_tenant: uuid.UUID,
) -> None:
    client, holder, _ = env
    _as(holder, fresh_tenant, "admin")
    resp = client.get("/api/v1/incidents", params={"status": "on-fire"})
    assert resp.status_code == 422


def test_list_assets_filters_by_criticality(
    env: tuple[TestClient, dict[str, RequestContext], _StubOPA],
    fresh_tenant: uuid.UUID,
) -> None:
    client, holder, _ = env
    _as(holder, fresh_tenant, "admin")
    client.post("/api/v1/assets", json={"name": "payments-api", "criticality": "critical"})
    client.post("/api/v1/assets", json={"name": "dev-laptop", "criticality": "low"})

    resp = client.get("/api/v1/assets", params={"criticality": "critical"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["name"] == "payments-api"


def test_list_assets_searches_name_and_identifier(
    env: tuple[TestClient, dict[str, RequestContext], _StubOPA],
    fresh_tenant: uuid.UUID,
) -> None:
    client, holder, _ = env
    _as(holder, fresh_tenant, "admin")
    client.post(
        "/api/v1/assets",
        json={"name": "prod-s3-audit", "identifier": "arn:aws:s3:::acme-audit-logs"},
    )
    client.post("/api/v1/assets", json={"name": "svc-billing"})

    resp = client.get("/api/v1/assets", params={"q": "acme-audit"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["total"] == 1


def test_list_assets_default_order_is_criticality_first(
    env: tuple[TestClient, dict[str, RequestContext], _StubOPA],
    fresh_tenant: uuid.UUID,
) -> None:
    client, holder, _ = env
    _as(holder, fresh_tenant, "admin")
    client.post("/api/v1/assets", json={"name": "low-crit", "criticality": "low"})
    client.post("/api/v1/assets", json={"name": "crit-crit", "criticality": "critical"})

    resp = client.get("/api/v1/assets")
    assert resp.status_code == 200, resp.text
    names = [item["name"] for item in resp.json()["items"]]
    assert names == ["crit-crit", "low-crit"]


def test_list_assets_rejects_unknown_criticality(
    env: tuple[TestClient, dict[str, RequestContext], _StubOPA],
    fresh_tenant: uuid.UUID,
) -> None:
    client, holder, _ = env
    _as(holder, fresh_tenant, "admin")
    resp = client.get("/api/v1/assets", params={"criticality": "meh"})
    assert resp.status_code == 422
