"""End-to-end tests for grounded Q&A, triage, ingestion, authz, and streaming (offline)."""

from __future__ import annotations

from typing import Any

from dula_ai_gateway.deps import RequestContext
from fastapi.testclient import TestClient

Env = tuple[TestClient, dict[str, RequestContext], Any]


def _as(holder: dict[str, RequestContext], tenant: str, *roles: str) -> None:
    holder["ctx"] = RequestContext(subject=f"u-{tenant}", tenant=tenant, roles=roles)


def test_ask_returns_grounded_cited_answer(env: Env) -> None:
    client, _, _ = env
    resp = client.post("/api/v1/ask", json={"question": "How do I defend against brute force?"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["grounded"] is True
    assert body["citations"]
    assert any(c["document_id"] == "attack-t1110" for c in body["citations"])
    assert "[1]" in body["answer"]


def test_ask_out_of_domain_is_not_grounded(env: Env) -> None:
    client, _, _ = env
    resp = client.post("/api/v1/ask", json={"question": "What is the capital of France?"})
    assert resp.status_code == 200
    assert resp.json()["grounded"] is False


def test_authz_denied_returns_403(env: Env) -> None:
    client, _, opa = env
    opa.allow_result = False
    resp = client.post("/api/v1/ask", json={"question": "How do I defend against brute force?"})
    assert resp.status_code == 403


def test_triage_produces_grounded_answer(env: Env) -> None:
    client, _, _ = env
    resp = client.post(
        "/api/v1/triage",
        json={"title": "Many failed logins from one host", "severity": "high"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["citations"]


def test_ingested_tenant_doc_is_retrievable_and_isolated(env: Env) -> None:
    client, holder, _ = env
    _as(holder, "tenant-a", "analyst")
    ing = client.post(
        "/api/v1/knowledge/documents",
        json={"text": "Our honeypot is host HP-7 on the DMZ subnet.", "source": "runbook"},
    )
    assert ing.status_code == 201, ing.text

    a = client.post("/api/v1/ask", json={"question": "What is our honeypot host?"})
    assert any(c["source"] == "runbook" for c in a.json()["citations"])

    # A different tenant must not retrieve tenant-a's private document.
    _as(holder, "tenant-b", "analyst")
    b = client.post("/api/v1/ask", json={"question": "What is our honeypot host?"})
    assert all(c["source"] != "runbook" for c in b.json()["citations"])


def test_ask_stream_emits_sse(env: Env) -> None:
    client, _, _ = env
    with client.stream(
        "POST", "/api/v1/ask/stream", json={"question": "What is Log4Shell?"}
    ) as resp:
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/event-stream")
        body = "".join(resp.iter_text())
    assert "data:" in body
    assert "event: done" in body
