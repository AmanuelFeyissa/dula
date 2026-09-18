"""The egress-brokered HTTP client and the real SIEM/ticketing backends, against mock feeds."""

from __future__ import annotations

import json
from collections.abc import Callable

import httpx
import pytest
from dula_plugins.builtin import BuiltinBackends, build_offline_host
from dula_plugins.connector import ConnectorContext, InMemorySecrets
from dula_plugins.connectors.siem import OpenSearchLogBackend
from dula_plugins.connectors.ticketing import HttpTicketBackend
from dula_plugins.egress import EgressError, EgressGuard, EgressPolicy
from dula_plugins.http import EgressHttpClient, HttpError

TENANT = "t1"


def _guard(*hosts: str, enabled: bool = True) -> EgressGuard:
    return EgressGuard(
        policy=EgressPolicy(allowed_hosts=frozenset(hosts), enabled=enabled), resolve=False
    )


def _ctx(guard: EgressGuard, secrets: dict[str, str] | None = None) -> ConnectorContext:
    return ConnectorContext(
        tenant=TENANT, subject="u1", egress=guard, secrets=InMemorySecrets(secrets or {})
    )


def _transport(handler: Callable[[httpx.Request], httpx.Response]) -> httpx.MockTransport:
    return httpx.MockTransport(handler)


# --- EgressHttpClient -------------------------------------------------------------------


async def test_client_refuses_undeclared_host_before_any_request() -> None:
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(200, json={})

    client = EgressHttpClient(_guard("allowed.example.com"), transport=_transport(handler))
    with pytest.raises(EgressError):
        await client.get_json("https://other.example.com/x")
    assert calls == []  # denied by the guard, never reached the transport


async def test_client_is_inert_when_egress_disabled() -> None:
    client = EgressHttpClient(_guard("allowed.example.com", enabled=False))
    with pytest.raises(EgressError):
        await client.get_json("https://allowed.example.com/x")


async def test_client_refuses_redirects() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(302, headers={"location": "https://evil.example.net/"})

    client = EgressHttpClient(_guard("allowed.example.com"), transport=_transport(handler))
    with pytest.raises(HttpError, match="redirect"):
        await client.get_json("https://allowed.example.com/x")


async def test_client_caps_response_size() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"x" * 2048)

    client = EgressHttpClient(
        _guard("allowed.example.com"), max_response_bytes=1024, transport=_transport(handler)
    )
    with pytest.raises(HttpError, match="exceeds"):
        await client.request("GET", "https://allowed.example.com/x")


async def test_client_maps_http_errors_and_non_json() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/500":
            return httpx.Response(500, text="boom")
        return httpx.Response(200, text="<html>")

    client = EgressHttpClient(_guard("allowed.example.com"), transport=_transport(handler))
    with pytest.raises(HttpError, match="HTTP 500"):
        await client.get_json("https://allowed.example.com/500")
    with pytest.raises(HttpError, match="not JSON"):
        await client.get_json("https://allowed.example.com/html")


# --- OpenSearchLogBackend ---------------------------------------------------------------


async def test_opensearch_backend_queries_tenant_index_and_normalizes_hits() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(
            200,
            json={
                "hits": {
                    "hits": [
                        {
                            "_source": {
                                "@timestamp": "2026-09-18T10:00:00Z",
                                "host": {"name": "HOST-7"},
                                "message": "connection to evil.example.com",
                            }
                        },
                        {"_source": {"ts": "2026-09-18T10:01:00Z", "msg": "beacon 60s"}},
                        {"_source": "not-an-object"},
                    ]
                }
            },
        )

    backend = OpenSearchLogBackend(
        base_url="https://siem.example.com:9200/", transport=_transport(handler)
    )
    ctx = _ctx(_guard("siem.example.com"), {"siem.authorization": "Basic abc"})
    events = await backend.query(TENANT, "evil.example.com", 5, ctx)

    req = seen[0]
    assert req.method == "POST"
    assert req.url.path == f"/logs-{TENANT}-*/_search"  # per-tenant index namespace
    assert req.headers["authorization"] == "Basic abc"
    body = json.loads(req.content)
    assert body["size"] == 5 and body["query"]["query_string"]["query"] == "evil.example.com"

    assert events == [
        {
            "ts": "2026-09-18T10:00:00Z",
            "host": "HOST-7",
            "message": "connection to evil.example.com",
        },
        {"ts": "2026-09-18T10:01:00Z", "host": "", "message": "beacon 60s"},
    ]


async def test_siem_connector_via_host_fails_closed_when_air_gapped(full_checker) -> None:
    def handler(request: httpx.Request) -> httpx.Response:  # pragma: no cover - must not run
        raise AssertionError("egress should have been denied before the transport")

    backends = BuiltinBackends(
        logs=OpenSearchLogBackend(
            base_url="https://siem.example.com", transport=_transport(handler)
        ),
        tickets=HttpTicketBackend(create_url="https://tickets.example.com/api"),
        siem_egress=["siem.example.com"],
        ticketing_egress=["tickets.example.com"],
    )
    host, _ = build_offline_host(
        full_checker, backends=backends, egress_enabled=False, resolve_egress=False
    )
    result = await host.invoke(
        "siem.search", {"query": "x"}, tenant=TENANT, subject="u1", roles=["analyst"]
    )
    assert not result.ok and "egress denied" in (result.error or "")


async def test_siem_connector_via_host_reaches_only_its_declared_host(full_checker) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"hits": {"hits": []}})

    backends = BuiltinBackends(
        logs=OpenSearchLogBackend(
            base_url="https://siem.example.com", transport=_transport(handler)
        ),
        tickets=HttpTicketBackend(create_url="https://tickets.example.com/api"),
        siem_egress=["siem.example.com"],
        ticketing_egress=["tickets.example.com"],
    )
    host, _ = build_offline_host(
        full_checker, backends=backends, egress_enabled=True, resolve_egress=False
    )
    ok = await host.invoke(
        "siem.search", {"query": "x"}, tenant=TENANT, subject="u1", roles=["analyst"]
    )
    assert ok.ok and ok.output == {"count": 0, "events": []}

    # The SIEM plugin's allowlist does not include the ticketing host and vice versa: a backend
    # pointed at a host outside its own manifest is denied even with egress globally enabled.
    stray = SiemStray(base_url="https://tickets.example.com", transport=_transport(handler))
    ctx = host.context_for("dula-plugin-dula-siem", tenant=TENANT, subject="u1")
    with pytest.raises(EgressError):
        await stray.query(TENANT, "x", 1, ctx)


class SiemStray(OpenSearchLogBackend):
    """Same backend class, mis-pointed at another plugin's host (for the allowlist test)."""


# --- HttpTicketBackend ------------------------------------------------------------------


async def test_http_ticket_backend_posts_with_idempotency_key() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(201, json={"key": "SEC-42", "status": "open"})

    backend = HttpTicketBackend(
        create_url="https://tickets.example.com/api/tickets",
        id_field="key",
        transport=_transport(handler),
    )
    ctx = _ctx(_guard("tickets.example.com"), {"ticketing.authorization": "Bearer t"})
    ticket_id = await backend.create(TENANT, "Beacon on HOST-7", "details", "run-1:step-4", ctx)

    assert ticket_id == "SEC-42"
    req = seen[0]
    assert req.method == "POST" and req.headers["authorization"] == "Bearer t"
    assert req.headers["idempotency-key"] == "run-1:step-4"
    assert json.loads(req.content) == {
        "title": "Beacon on HOST-7",
        "body": "details",
        "tenant": TENANT,
    }


async def test_http_ticket_backend_rejects_response_without_id() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"status": "queued"})

    backend = HttpTicketBackend(
        create_url="https://tickets.example.com/api/tickets", transport=_transport(handler)
    )
    with pytest.raises(HttpError, match="no 'id'"):
        await backend.create(TENANT, "t", "b", None, _ctx(_guard("tickets.example.com")))


async def test_ticketing_connector_surfaces_backend_failure_as_result(full_checker) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="down")

    backends = BuiltinBackends(
        logs=OpenSearchLogBackend(base_url="https://siem.example.com"),
        tickets=HttpTicketBackend(
            create_url="https://tickets.example.com/api", transport=_transport(handler)
        ),
        siem_egress=["siem.example.com"],
        ticketing_egress=["tickets.example.com"],
    )
    host, _ = build_offline_host(
        full_checker, backends=backends, egress_enabled=True, resolve_egress=False
    )
    result = await host.invoke(
        "ticketing.create_ticket",
        {"title": "t"},
        tenant=TENANT,
        subject="u1",
        roles=["analyst"],
    )
    assert not result.ok and "HTTP 503" in (result.error or "")
