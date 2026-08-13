"""End-to-end tests for plugin/connector endpoints + the agent→connector bridge (offline)."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest
from dula_ai_gateway.agents_wiring import build_agent_subsystem
from dula_ai_gateway.config import Settings
from dula_ai_gateway.deps import RequestContext, get_request_context
from dula_ai_gateway.main import create_app
from dula_ai_gateway.plugins_wiring import build_plugins_subsystem
from fastapi.testclient import TestClient


class ActionOPA:
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
        _wire(client, allowed=None)
        yield client, holder


def _wire(client: TestClient, allowed: set[str] | None) -> None:
    opa = ActionOPA(allowed=allowed)
    plugins = build_plugins_subsystem(opa)
    client.app.state.opa = opa  # type: ignore[attr-defined]
    client.app.state.plugins = plugins  # type: ignore[attr-defined]
    client.app.state.agents = build_agent_subsystem(opa, plugins)  # type: ignore[attr-defined]


def test_list_plugins(env: tuple[TestClient, Holder]) -> None:
    client, _ = env
    resp = client.get("/api/v1/plugins")
    assert resp.status_code == 200, resp.text
    ids = {p["id"] for p in resp.json()}
    assert ids == {"dula-plugin-dula-siem", "dula-plugin-dula-ti", "dula-plugin-dula-ticketing"}
    assert all(p["state"] == "enabled" for p in resp.json())


def test_invoke_read_connector(env: tuple[TestClient, Holder]) -> None:
    client, _ = env
    resp = client.post("/api/v1/connectors/siem.search/invoke", json={"args": {"query": "HOST-7"}})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["ok"] is True and body["untrusted"] is True
    assert body["output"]["events"][0]["source"] == "siem"


def test_invoke_ti_lookup(env: tuple[TestClient, Holder]) -> None:
    client, _ = env
    resp = client.post(
        "/api/v1/connectors/ti.lookup_indicator/invoke", json={"args": {"value": "evil.com"}}
    )
    assert resp.status_code == 200, resp.text
    reps = {i["value"]: i["reputation"] for i in resp.json()["output"]["indicators"]}
    assert reps.get("evil.com") == "malicious"


def test_consequential_connector_rejected(env: tuple[TestClient, Holder]) -> None:
    client, _ = env
    resp = client.post(
        "/api/v1/connectors/ticketing.create_ticket/invoke", json={"args": {"title": "x"}}
    )
    assert resp.status_code == 409  # must run through an agent (approval-gated)


def test_unknown_capability_404(env: tuple[TestClient, Holder]) -> None:
    client, _ = env
    resp = client.post("/api/v1/connectors/nope.nope/invoke", json={"args": {}})
    assert resp.status_code == 404


def test_invoke_endpoint_authz_denied(env: tuple[TestClient, Holder]) -> None:
    client, _ = env
    _wire(client, allowed=set())  # deny everything
    resp = client.post("/api/v1/connectors/siem.search/invoke", json={"args": {"query": "x"}})
    assert resp.status_code == 403


def test_invoke_per_capability_denied(env: tuple[TestClient, Holder]) -> None:
    client, _ = env
    # Endpoint allowed, but the specific capability permission is not → host denies → 403.
    _wire(client, allowed={"connectors.invoke"})
    resp = client.post("/api/v1/connectors/siem.search/invoke", json={"args": {"query": "x"}})
    assert resp.status_code == 403


def test_air_gapped_live_lookup_inert(env: tuple[TestClient, Holder]) -> None:
    client, _ = env
    resp = client.post(
        "/api/v1/connectors/ti.live_lookup/invoke", json={"args": {"value": "evil.com"}}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is False and "egress denied" in body["error"]


def test_enable_disable_admin(env: tuple[TestClient, Holder]) -> None:
    client, _ = env
    dis = client.post("/api/v1/plugins/dula-plugin-dula-siem/disable")
    assert dis.status_code == 204
    state = {p["id"]: p["state"] for p in client.get("/api/v1/plugins").json()}
    assert state["dula-plugin-dula-siem"] == "disabled"
    assert client.post("/api/v1/plugins/dula-plugin-dula-siem/enable").status_code == 204


def test_admin_denied_without_permission(env: tuple[TestClient, Holder]) -> None:
    client, _ = env
    _wire(client, allowed={"plugins.read"})  # no plugins.admin
    assert client.post("/api/v1/plugins/dula-plugin-dula-siem/disable").status_code == 403


def test_agent_uses_connector_backed_tools(env: tuple[TestClient, Holder]) -> None:
    client, _ = env
    # The agent's search_logs + create_ticket are connector-backed; the run corroborates via
    # the SIEM connector and pauses on the consequential (connector) ticket for approval.
    resp = client.post("/api/v1/agents/runs", json={"goal": "Investigate the beacon"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["state"] == "awaiting_approval"
    tools = [s["tool"] for s in body["steps"]]
    assert "search_logs" in tools and body["pending_approval"]["tool"] == "create_ticket"
    search_step = next(s for s in body["steps"] if s["tool"] == "search_logs")
    assert search_step["executed_ok"] is True
