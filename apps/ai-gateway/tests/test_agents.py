"""End-to-end tests for the agent endpoints (offline): run, approve/reject, authz, isolation."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest
from dula_ai_gateway.agents_wiring import build_agent_subsystem
from dula_ai_gateway.config import Settings
from dula_ai_gateway.deps import RequestContext, get_request_context
from dula_ai_gateway.main import create_app
from fastapi.testclient import TestClient


class ActionOPA:
    """Stub OPA that authorizes by action name (None = allow all)."""

    def __init__(self, allowed: set[str] | None = None) -> None:
        self.allowed = allowed

    async def allow(self, input_doc: dict[str, Any]) -> bool:
        return self.allowed is None or input_doc.get("action") in self.allowed


Holder = dict[str, RequestContext]


@pytest.fixture
def env() -> Iterator[tuple[TestClient, Holder]]:
    settings = Settings(profile="offline", events_enabled=False, seed_demo_corpus=False)
    app = create_app(settings)
    holder: Holder = {
        "ctx": RequestContext(subject="analyst-1", tenant="tenant-x", roles=("analyst",))
    }
    app.dependency_overrides[get_request_context] = lambda: holder["ctx"]
    with TestClient(app) as client:
        opa = ActionOPA(allowed=None)  # allow all by default
        client.app.state.opa = opa  # type: ignore[attr-defined]
        client.app.state.agents = build_agent_subsystem(opa)  # type: ignore[attr-defined]
        yield client, holder


def _as(holder: Holder, tenant: str, *roles: str) -> None:
    holder["ctx"] = RequestContext(subject=f"u-{tenant}", tenant=tenant, roles=roles)


def _set_opa(client: TestClient, allowed: set[str] | None) -> None:
    opa = ActionOPA(allowed=allowed)
    client.app.state.opa = opa  # type: ignore[attr-defined]
    client.app.state.agents = build_agent_subsystem(opa)  # type: ignore[attr-defined]


def test_start_run_pauses_for_approval(env: tuple[TestClient, Holder]) -> None:
    client, _ = env
    resp = client.post("/api/v1/agents/runs", json={"goal": "Investigate the beacon"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["state"] == "awaiting_approval"
    assert body["pending_approval"]["tool"] == "create_ticket"
    tools = [s["tool"] for s in body["steps"]]
    assert tools[:3] == ["list_alerts", "enrich_indicator", "search_logs"]
    assert all(s["executed_ok"] for s in body["steps"][:3])


def test_get_run_returns_trace(env: tuple[TestClient, Holder]) -> None:
    client, _ = env
    run_id = client.post("/api/v1/agents/runs", json={"goal": "Investigate"}).json()["run_id"]
    resp = client.get(f"/api/v1/agents/runs/{run_id}")
    assert resp.status_code == 200
    assert resp.json()["run_id"] == run_id


def test_approve_completes_and_creates_ticket(env: tuple[TestClient, Holder]) -> None:
    client, _ = env
    run_id = client.post("/api/v1/agents/runs", json={"goal": "Investigate"}).json()["run_id"]
    resp = client.post(f"/api/v1/agents/runs/{run_id}/approval", json={"approved": True})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["state"] == "completed"
    assert body["steps"][-1]["approved"] is True and body["steps"][-1]["executed_ok"] is True


def test_reject_halts_without_action(env: tuple[TestClient, Holder]) -> None:
    client, _ = env
    run_id = client.post("/api/v1/agents/runs", json={"goal": "Investigate"}).json()["run_id"]
    resp = client.post(f"/api/v1/agents/runs/{run_id}/approval", json={"approved": False})
    assert resp.status_code == 200
    body = resp.json()
    assert body["state"] == "halted"
    assert body["steps"][-1]["executed_ok"] is None  # ticket never executed


def test_double_approval_conflicts(env: tuple[TestClient, Holder]) -> None:
    client, _ = env
    run_id = client.post("/api/v1/agents/runs", json={"goal": "Investigate"}).json()["run_id"]
    client.post(f"/api/v1/agents/runs/{run_id}/approval", json={"approved": True})
    again = client.post(f"/api/v1/agents/runs/{run_id}/approval", json={"approved": True})
    assert again.status_code == 409


def test_start_run_authz_denied(env: tuple[TestClient, Holder]) -> None:
    client, _ = env
    _set_opa(client, allowed=set())  # deny everything
    resp = client.post("/api/v1/agents/runs", json={"goal": "Investigate"})
    assert resp.status_code == 403


def test_unauthorized_tool_halts_run(env: tuple[TestClient, Holder]) -> None:
    client, _ = env
    # The endpoint is allowed, but the user cannot create tickets → the run halts at that step,
    # with no ticket, rather than pausing for approval.
    _set_opa(
        client,
        allowed={
            "agents.run",
            "agents.read",
            "tool.list_alerts",
            "tool.enrich_indicator",
            "tool.search_logs",
        },
    )
    resp = client.post("/api/v1/agents/runs", json={"goal": "Investigate"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["state"] == "halted"
    assert body["pending_approval"] is None


def test_unknown_agent_is_404(env: tuple[TestClient, Holder]) -> None:
    client, _ = env
    resp = client.post("/api/v1/agents/runs", json={"agent": "nope", "goal": "x"})
    assert resp.status_code == 404


def test_run_not_found_is_404(env: tuple[TestClient, Holder]) -> None:
    client, _ = env
    assert client.get("/api/v1/agents/runs/does-not-exist").status_code == 404


def test_tenant_isolation_on_read(env: tuple[TestClient, Holder]) -> None:
    client, holder = env
    _as(holder, "tenant-a", "analyst")
    run_id = client.post("/api/v1/agents/runs", json={"goal": "Investigate"}).json()["run_id"]
    # A different tenant must not read tenant-a's run.
    _as(holder, "tenant-b", "analyst")
    assert client.get(f"/api/v1/agents/runs/{run_id}").status_code == 404
