"""Integration tests for PostgresRunStore against a real Postgres (ADR-0016).

Mirrors the skip-when-no-Postgres pattern in
apps/platform-api/tests/test_domain_integration.py: these run against the dev stack
(`docker compose up postgres` + `alembic upgrade head` in apps/ai-gateway) or a database
pointed to by ``DULA_TEST_DATABASE_URL``, and are skipped automatically otherwise (e.g. the
CI unit lane). InMemoryRunStore remains the default everywhere else, so this file is the
only place PostgresRunStore is exercised.
"""

from __future__ import annotations

import asyncio
import os
import uuid
from collections.abc import Iterator
from typing import Any

import pytest
from dula_agents.types import (
    ApprovalDecision,
    RunRecord,
    RunState,
    SideEffect,
    Step,
    ToolResult,
)
from dula_ai_gateway.config import Settings
from dula_ai_gateway.deps import RequestContext, get_request_context
from dula_ai_gateway.main import create_app
from dula_ai_gateway.models import Base
from dula_ai_gateway.run_store_postgres import PostgresRunStore
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

TEST_DB_URL = os.environ.get(
    "DULA_TEST_DATABASE_URL",
    "postgresql+asyncpg://dula:dula_dev_password@localhost:5432/dula",
)
TENANT_A = str(uuid.uuid4())
TENANT_B = str(uuid.uuid4())


async def _prepare_schema() -> None:
    engine = create_async_engine(TEST_DB_URL)
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
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
def store(_schema: None) -> PostgresRunStore:
    # A fresh engine per test, used entirely within one pytest-asyncio event loop (asyncio_mode
    # = "auto" in pyproject.toml) — asyncpg connections are loop-bound, so sharing an engine
    # across separate `asyncio.run()` calls (each with its own loop) breaks on Windows.
    engine = create_async_engine(TEST_DB_URL)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    return PostgresRunStore(maker, kind="agent")


def _record(tenant: str, *, run_id: str | None = None) -> RunRecord:
    return RunRecord(
        run_id=run_id or uuid.uuid4().hex,
        agent="investigation-assistant",
        goal="investigate the beacon",
        tenant=tenant,
        subject="user-a",
        state=RunState.AWAITING_APPROVAL,
        steps=[
            Step(
                index=0,
                thought="check the alert",
                tool="list_open_alerts",
                args={"limit": 5},
                side_effect=SideEffect.READ,
                permitted=True,
                result=ToolResult(ok=True, output={"alerts": []}),
            ),
            Step(
                index=1,
                thought="isolate the host",
                tool="isolate_host",
                args={"host": "HOST-7"},
                side_effect=SideEffect.CONSEQUENTIAL,
                permitted=True,
            ),
        ],
    )


async def test_save_then_get_round_trips_a_run(store: PostgresRunStore) -> None:
    record = _record(TENANT_A)

    await store.save(record, roles=("responder",))
    stored = await store.get(TENANT_A, record.run_id)

    assert stored is not None
    assert stored.roles == ("responder",)
    assert stored.record.run_id == record.run_id
    assert stored.record.agent == "investigation-assistant"
    assert stored.record.state is RunState.AWAITING_APPROVAL
    assert len(stored.record.steps) == 2
    assert stored.record.steps[0].tool == "list_open_alerts"
    assert stored.record.steps[0].result is not None
    assert stored.record.steps[0].result.output == {"alerts": []}
    assert stored.record.steps[1].tool == "isolate_host"
    assert stored.record.steps[1].args == {"host": "HOST-7"}


async def test_get_returns_none_for_unknown_run(store: PostgresRunStore) -> None:
    assert await store.get(TENANT_A, uuid.uuid4().hex) is None


async def test_get_enforces_tenant_isolation(store: PostgresRunStore) -> None:
    record = _record(TENANT_A)
    await store.save(record, roles=("responder",))

    # Tenant B must never see tenant A's run — not even by guessing the run_id.
    assert await store.get(TENANT_B, record.run_id) is None


async def test_save_replaces_steps_rather_than_accumulating(store: PostgresRunStore) -> None:
    record = _record(TENANT_A)
    await store.save(record, roles=("responder",))

    # Simulate approval: the runtime appends the resolved decision and marks it executed,
    # then the router calls save() again with the *same* run_id and the full updated trace.
    record.steps[1].approval = ApprovalDecision(
        approved=True, approver="raj", approver_username="raj"
    )
    record.steps[1].result = ToolResult(ok=True, output={"isolated": True})
    record.state = RunState.COMPLETED
    record.result = "Host isolated."
    await store.save(record, roles=("responder",))

    stored = await store.get(TENANT_A, record.run_id)
    assert stored is not None
    assert stored.record.state is RunState.COMPLETED
    assert stored.record.result == "Host isolated."
    # Still exactly 2 steps — not 4 — proving the second save replaced rather than appended.
    assert len(stored.record.steps) == 2
    assert stored.record.steps[1].approval is not None
    assert stored.record.steps[1].approval.approved is True
    assert stored.record.steps[1].approval.approver_label == "raj"


async def test_kind_separates_agent_and_automation_runs(_schema: None) -> None:
    engine = create_async_engine(TEST_DB_URL)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    agent_store = PostgresRunStore(maker, kind="agent")
    automation_store = PostgresRunStore(maker, kind="automation")

    record = _record(TENANT_A)
    await agent_store.save(record, roles=("analyst",))

    # A run saved under "agent" must not be visible through the "automation" store, even
    # for the same tenant and run_id — the two run pools stay logically separate.
    assert await automation_store.get(TENANT_A, record.run_id) is None
    assert await agent_store.get(TENANT_A, record.run_id) is not None


class _AllowAllOPA:
    async def allow(self, _input_doc: dict[str, Any]) -> bool:
        return True


def test_run_survives_an_app_restart_via_postgres(_schema: None) -> None:
    """The literal PR E acceptance test (M010 plan, item E, verification step 7): start a
    run, approve its consequential step, tear the app down — simulating
    `docker compose restart ai-gateway` — then stand up a *separate* app instance against
    the same database and confirm the run and its approval are still there over HTTP."""
    settings = Settings(
        profile="offline", events_enabled=False, run_store="postgres", database_url=TEST_DB_URL
    )
    tenant = str(uuid.uuid4())
    ctx = RequestContext(subject="raj-sub", tenant=tenant, roles=("responder",), username="raj")

    app1 = create_app(settings)
    app1.dependency_overrides[get_request_context] = lambda: ctx
    with TestClient(app1) as client1:
        client1.app.state.opa = _AllowAllOPA()  # type: ignore[attr-defined]

        started = client1.post("/api/v1/agents/runs", json={"goal": "Investigate the beacon"})
        assert started.status_code == 200, started.text
        run_id = started.json()["run_id"]
        assert started.json()["state"] == "awaiting_approval"

        approved = client1.post(f"/api/v1/agents/runs/{run_id}/approval", json={"approved": True})
        assert approved.status_code == 200, approved.text
        assert approved.json()["state"] == "completed"
    # `with` exits here: lifespan's `finally` runs, disposing app1's engine — the closest a
    # TestClient gets to a real process exit.

    app2 = create_app(settings)
    app2.dependency_overrides[get_request_context] = lambda: ctx
    with TestClient(app2) as client2:
        client2.app.state.opa = _AllowAllOPA()  # type: ignore[attr-defined]

        fetched = client2.get(f"/api/v1/agents/runs/{run_id}")
        assert fetched.status_code == 200, fetched.text
        body = fetched.json()
        assert body["run_id"] == run_id
        assert body["state"] == "completed"
        approved_step = next(s for s in body["steps"] if s["approved"] is not None)
        assert approved_step["approved"] is True
        assert approved_step["approved_by"] == "raj"
