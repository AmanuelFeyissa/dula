"""The ADR-0013 baseline runner: a real spawned worker with host-brokered HTTP + secrets."""

from __future__ import annotations

import os

import httpx
from dula_plugins.connector import ConnectorContext, InMemorySecrets
from dula_plugins.connectors.ti import ThreatIntelConnector
from dula_plugins.egress import EgressGuard, EgressPolicy
from dula_plugins.sandbox import SandboxSpec, SubprocessRunner
from dula_plugins.sandbox_worker import SECRET_REF_PREFIX, BrokeredSecrets
from dula_plugins.testing import ProbeConnector

TENANT = "t1"


def _ctx(
    *hosts: str, enabled: bool = True, secrets: dict[str, str] | None = None
) -> ConnectorContext:
    return ConnectorContext(
        tenant=TENANT,
        subject="u1",
        egress=EgressGuard(
            policy=EgressPolicy(allowed_hosts=frozenset(hosts), enabled=enabled), resolve=False
        ),
        secrets=InMemorySecrets(secrets or {}),
    )


async def test_worker_runs_in_another_process() -> None:
    spec = SandboxSpec(timeout_seconds=60, max_output_bytes=10_000)
    result = await SubprocessRunner().run(ProbeConnector(), "probe.pid", {}, _ctx(), spec)
    assert result.ok and result.output["pid"] != os.getpid()
    assert result.untrusted


async def test_worker_never_sees_secret_values() -> None:
    spec = SandboxSpec(timeout_seconds=60, max_output_bytes=10_000)
    ctx = _ctx(secrets={"ti.authorization": "Bearer real-token"})
    result = await SubprocessRunner().run(
        ProbeConnector(), "probe.secret", {"key": "ti.authorization"}, ctx, spec
    )
    assert result.ok and result.output["seen"] == f"{SECRET_REF_PREFIX}ti.authorization"
    assert BrokeredSecrets().get("x") == f"{SECRET_REF_PREFIX}x"


async def test_brokered_http_goes_through_host_guard_and_substitutes_secret() -> None:
    seen: list[httpx.Request] = []

    def feed(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"verdict": "malicious"})

    runner = SubprocessRunner(transport=httpx.MockTransport(feed))
    ctx = _ctx("ti.example.com", secrets={"ti.authorization": "Bearer real-token"})
    spec = SandboxSpec(timeout_seconds=60, max_output_bytes=10_000)
    result = await runner.run(
        ThreatIntelConnector(feed_host="ti.example.com"),
        "ti.live_lookup",
        {"value": "evil.com"},
        ctx,
        spec,
    )
    assert result.ok and result.output["response"] == {"verdict": "malicious"}
    # The request was made by the host (this process' mock transport), with the real secret
    # value substituted for the reference the worker put in the header.
    assert seen[0].headers["authorization"] == "Bearer real-token"
    assert seen[0].url.host == "ti.example.com"


async def test_brokered_http_is_denied_by_host_when_egress_disabled() -> None:
    def feed(request: httpx.Request) -> httpx.Response:  # pragma: no cover - must not run
        raise AssertionError("host must deny before any request")

    runner = SubprocessRunner(transport=httpx.MockTransport(feed))
    spec = SandboxSpec(timeout_seconds=60, max_output_bytes=10_000)
    result = await runner.run(
        ThreatIntelConnector(feed_host="ti.example.com"),
        "ti.live_lookup",
        {"value": "evil.com"},
        _ctx("ti.example.com", enabled=False),
        spec,
    )
    assert not result.ok and "egress denied" in (result.error or "")


async def test_worker_is_killed_at_the_wall_time_limit() -> None:
    spec = SandboxSpec(timeout_seconds=3, max_output_bytes=10_000)
    result = await SubprocessRunner().run(
        ProbeConnector(), "probe.sleep", {"seconds": 60}, _ctx(), spec
    )
    assert not result.ok and result.error == "connector timed out"


async def test_worker_crash_is_a_failed_result_not_a_host_exception() -> None:
    spec = SandboxSpec(timeout_seconds=60, max_output_bytes=10_000)
    result = await SubprocessRunner().run(ProbeConnector(), "probe.crash", {}, _ctx(), spec)
    assert not result.ok and "boom" in (result.error or "")
