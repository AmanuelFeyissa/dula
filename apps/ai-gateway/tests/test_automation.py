"""End-to-end tests for the automation (playbook) endpoints: run, approve, report, authz, isolation.

A playbook run is executed by the shared agent runtime, so the consequential ticket step pauses
for approval exactly like an agent run — and no unauthorized/unapproved action ever executes.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest
from dula_ai_gateway.agents_wiring import build_agent_subsystem
from dula_ai_gateway.automation_wiring import build_automation_subsystem
from dula_ai_gateway.config import Settings
from dula_ai_gateway.deps import RequestContext, get_request_context
from dula_ai_gateway.main import create_app
from fastapi.testclient import TestClient


class ActionOPA:
    def __init__(self, allowed: set[str] | None = None) -> None:
        self.allowed = allowed

    async def allow(self, input_doc: dict[str, Any]) -> bool:
        return self.allowed is None or input_doc.get("action") in self.allowed


Holder = dict[str, RequestContext]


def _wire(client: TestClient, opa: ActionOPA) -> None:
    agents = build_agent_subsystem(opa)
    client.app.state.opa = opa  # type: ignore[attr-defined]
    client.app.state.agents = agents  # type: ignore[attr-defined]
    client.app.state.automation = build_automation_subsystem(agents)  # type: ignore[attr-defined]


@pytest.fixture
def env() -> Iterator[tuple[TestClient, Holder]]:
    settings = Settings(profile="offline", events_enabled=False, seed_demo_corpus=False)
    app = create_app(settings)
    holder: Holder = {
        "ctx": RequestContext(subject="analyst-1", tenant="tenant-x", roles=("analyst",))
    }
    app.dependency_overrides[get_request_context] = lambda: holder["ctx"]
    with TestClient(app) as client:
        _wire(client, ActionOPA(allowed=None))
        yield client, holder


def _as(holder: Holder, tenant: str, *roles: str) -> None:
    holder["ctx"] = RequestContext(subject=f"u-{tenant}", tenant=tenant, roles=roles)


def _start(client: TestClient, name: str = "triage-enrich-ticket") -> dict[str, Any]:
    resp = client.post(f"/api/v1/automation/playbooks/{name}/runs", json={"goal": "Investigate"})
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_list_playbooks(env: tuple[TestClient, Holder]) -> None:
    client, _ = env
    resp = client.get("/api/v1/automation/playbooks")
    assert resp.status_code == 200
    names = [p["name"] for p in resp.json()]
    assert "triage-enrich-ticket" in names
    steps = next(p for p in resp.json() if p["name"] == "triage-enrich-ticket")["steps"]
    assert [s["tool"] for s in steps] == [
        "list_alerts",
        "enrich_indicator",
        "search_logs",
        "create_ticket",
    ]


def test_run_pauses_for_approval(env: tuple[TestClient, Holder]) -> None:
    client, _ = env
    body = _start(client)
    assert body["state"] == "awaiting_approval"
    assert body["pending_approval"]["tool"] == "create_ticket"
    assert body["playbook"] == "triage-enrich-ticket"
    assert [s["tool"] for s in body["steps"][:3]] == [
        "list_alerts",
        "enrich_indicator",
        "search_logs",
    ]


def test_approve_completes_then_report_is_grounded(env: tuple[TestClient, Holder]) -> None:
    client, _ = env
    run_id = _start(client)["run_id"]
    approved = client.post(f"/api/v1/automation/runs/{run_id}/approval", json={"approved": True})
    assert approved.status_code == 200, approved.text
    assert approved.json()["state"] == "completed"

    report = client.get(f"/api/v1/automation/runs/{run_id}/report")
    assert report.status_code == 200, report.text
    rb = report.json()
    kinds = {e["kind"] for e in rb["evidence"]}
    assert {"alert", "ticket"} <= kinds
    assert "untrusted evidence" in rb["markdown"]
    assert rb["state"] == "completed"


def test_reject_halts_and_report_claims_no_ticket(env: tuple[TestClient, Holder]) -> None:
    client, _ = env
    run_id = _start(client)["run_id"]
    resp = client.post(f"/api/v1/automation/runs/{run_id}/approval", json={"approved": False})
    assert resp.json()["state"] == "halted"
    report = client.get(f"/api/v1/automation/runs/{run_id}/report").json()
    assert not any(e["kind"] == "ticket" for e in report["evidence"])


def test_run_authz_denied(env: tuple[TestClient, Holder]) -> None:
    client, _ = env
    _wire(client, ActionOPA(allowed=set()))
    resp = client.post("/api/v1/automation/playbooks/triage-enrich-ticket/runs", json={"goal": "x"})
    assert resp.status_code == 403


def test_unauthorized_ticket_halts_without_action(env: tuple[TestClient, Holder]) -> None:
    client, _ = env
    _wire(
        client,
        ActionOPA(
            allowed={
                "automation.run",
                "automation.read",
                "tool.list_alerts",
                "tool.enrich_indicator",
                "tool.search_logs",
            }
        ),
    )
    body = _start(client)
    assert body["state"] == "halted"
    assert body["pending_approval"] is None
    assert not any(s["tool"] == "create_ticket" and s["executed_ok"] for s in body["steps"])


def test_unknown_playbook_is_404(env: tuple[TestClient, Holder]) -> None:
    client, _ = env
    resp = client.post("/api/v1/automation/playbooks/nope/runs", json={"goal": "x"})
    assert resp.status_code == 404


def test_tenant_isolation_on_read(env: tuple[TestClient, Holder]) -> None:
    client, holder = env
    _as(holder, "tenant-a", "analyst")
    run_id = _start(client)["run_id"]
    _as(holder, "tenant-b", "analyst")
    assert client.get(f"/api/v1/automation/runs/{run_id}").status_code == 404
    assert client.get(f"/api/v1/automation/runs/{run_id}/report").status_code == 404


# --- Triggers ----------------------------------------------------------------------------


def test_trigger_create_fire_and_runs_as_creator(env: tuple[TestClient, Holder]) -> None:
    client, holder = env
    resp = client.post(
        "/api/v1/automation/triggers",
        json={"playbook": "triage-enrich-ticket", "goal": "Hourly sweep", "interval_seconds": 3600},
    )
    assert resp.status_code == 201, resp.text
    trigger = resp.json()
    assert trigger["kind"] == "interval" and trigger["subject"] == "analyst-1"
    assert trigger["roles"] == ["analyst"] and trigger["next_fire_at"] is not None

    listed = client.get("/api/v1/automation/triggers").json()
    assert [t["id"] for t in listed] == [trigger["id"]]

    # Another tenant sees nothing and cannot fire or disable it.
    _as(holder, "tenant-y", "analyst")
    assert client.get("/api/v1/automation/triggers").json() == []
    assert client.post(f"/api/v1/automation/triggers/{trigger['id']}/fire").status_code == 404
    assert client.delete(f"/api/v1/automation/triggers/{trigger['id']}").status_code == 404

    # A responder in the owning tenant fires it manually: the run acts as the creator (analyst-1
    # with the analyst role), and the consequential ticket step still waits for a human.
    holder["ctx"] = RequestContext(subject="responder-9", tenant="tenant-x", roles=("responder",))
    fired = client.post(f"/api/v1/automation/triggers/{trigger['id']}/fire")
    assert fired.status_code == 200, fired.text
    run = fired.json()
    assert run["goal"] == "Hourly sweep" and run["state"] == "awaiting_approval"
    stored = client.get(f"/api/v1/automation/runs/{run['run_id']}").json()
    assert stored["run_id"] == run["run_id"]
    automation = client.app.state.automation  # type: ignore[attr-defined]
    saved = automation.store._runs[run["run_id"]]
    assert saved.record.subject == "analyst-1" and saved.roles == ("analyst",)

    disabled = client.delete(f"/api/v1/automation/triggers/{trigger['id']}")
    assert disabled.status_code == 200 and disabled.json()["enabled"] is False
    assert client.post(f"/api/v1/automation/triggers/{trigger['id']}/fire").status_code == 404


def test_trigger_validation_and_authz(env: tuple[TestClient, Holder]) -> None:
    client, _ = env
    both = client.post(
        "/api/v1/automation/triggers",
        json={"playbook": "triage-enrich-ticket", "interval_seconds": 600, "event_type": "x"},
    )
    assert both.status_code == 422
    unknown = client.post(
        "/api/v1/automation/triggers", json={"playbook": "nope", "interval_seconds": 600}
    )
    assert unknown.status_code == 404

    _wire(client, ActionOPA(allowed={"automation.read", "automation.run"}))  # no .schedule
    denied = client.post(
        "/api/v1/automation/triggers",
        json={"playbook": "triage-enrich-ticket", "interval_seconds": 600},
    )
    assert denied.status_code == 403
