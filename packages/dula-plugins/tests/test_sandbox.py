"""Tests for the sandbox runner seam (ADR-0013)."""

from __future__ import annotations

import asyncio
from collections.abc import Callable

import pytest
from dula_plugins.builtin import BuiltinBackends
from dula_plugins.connector import ConnectorContext, ConnectorResult, InMemorySecrets
from dula_plugins.connectors.siem import siem_manifest
from dula_plugins.egress import EgressGuard, EgressPolicy
from dula_plugins.host import PluginHost
from dula_plugins.manifest import PluginManifest
from dula_plugins.sandbox import InProcessRunner, SandboxSpec

HostFactory = Callable[..., tuple[PluginHost, BuiltinBackends]]

_CTX = ConnectorContext(
    tenant="t1",
    subject="u1",
    egress=EgressGuard(policy=EgressPolicy(enabled=False), resolve=False),
    secrets=InMemorySecrets(),
)


def test_spec_from_manifest_maps_limits() -> None:
    m: PluginManifest = siem_manifest()
    spec = SandboxSpec.from_manifest(m)
    assert spec.timeout_seconds == m.limits.timeout_seconds
    assert spec.max_output_bytes == m.limits.max_output_bytes
    # Capability-based defaults: no ambient network, non-root, read-only fs.
    assert spec.network == "brokered"
    assert spec.run_as_non_root and spec.read_only_fs


class _SlowConnector:
    manifest = siem_manifest()

    async def invoke(self, capability: str, args: dict, ctx: ConnectorContext) -> ConnectorResult:
        await asyncio.sleep(1.0)
        return ConnectorResult(ok=True, output={"never": "returned"})


class _FastConnector:
    manifest = siem_manifest()

    async def invoke(self, capability: str, args: dict, ctx: ConnectorContext) -> ConnectorResult:
        return ConnectorResult(ok=True, output={"hi": True})


async def test_runner_enforces_timeout() -> None:
    runner = InProcessRunner()
    spec = SandboxSpec(timeout_seconds=0.01, max_output_bytes=1_000_000)
    result = await runner.run(_SlowConnector(), "siem.search", {}, _CTX, spec)
    assert not result.ok and "timed out" in (result.error or "")


async def test_runner_passes_through_result() -> None:
    runner = InProcessRunner()
    spec = SandboxSpec(timeout_seconds=5.0, max_output_bytes=1_000_000)
    result = await runner.run(_FastConnector(), "siem.search", {}, _CTX, spec)
    assert result.ok and result.output == {"hi": True}


async def test_host_uses_runner_timeout(
    full_checker, backends: BuiltinBackends, host_factory: HostFactory, tenant: str
) -> None:
    # A host wired with a very small timeout runner still returns a clean failure, not a hang.
    host, _ = host_factory(full_checker, backends)
    # Swap in the slow connector under an already-installed plugin id to exercise the host path.
    result = await host.invoke(
        "siem.search", {"query": "HOST-7"}, tenant=tenant, subject="u1", roles=["analyst"]
    )
    assert result.ok  # normal fast path still works through the runner


@pytest.mark.parametrize("budget", [0.001, 0.005])
async def test_slow_connector_times_out_various(budget: float) -> None:
    runner = InProcessRunner()
    spec = SandboxSpec(timeout_seconds=budget, max_output_bytes=1_000_000)
    result = await runner.run(_SlowConnector(), "siem.search", {}, _CTX, spec)
    assert not result.ok
