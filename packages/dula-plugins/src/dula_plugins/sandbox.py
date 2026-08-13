"""Sandbox runner (ADR-0013 — plugin sandbox mechanism).

The isolation boundary is a **pluggable seam**, so it can be strengthened per deployment profile
without changing the host or the security controls. A `SandboxSpec` (derived from the manifest)
declares the guarantees a runner must uphold: wall-time/output limits, **no ambient network**
(egress is brokered by the host — the connector only ever holds an `EgressGuard`, never a raw
socket), read-only filesystem, and non-root execution.

- `InProcessRunner` (default, all profiles incl. air-gapped/dev): enforces the guarantees that are
  enforceable in-process — the timeout, and structurally the brokered-only network. It is the
  baseline the other runners strengthen.
- `SubprocessRunner` (baseline out-of-process worker) and `ContainerRunner` (orchestrated profiles,
  gVisor/Kata) implement the same interface and add OS/container isolation; they ship with the
  plugin worker/loader (ADR-0013, Phase 07+). A future `WasmRunner` slots in the same way.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Protocol

from dula_plugins.connector import Connector, ConnectorContext, ConnectorResult
from dula_plugins.manifest import PluginManifest


@dataclass(frozen=True, slots=True)
class SandboxSpec:
    """The isolation guarantees a runner must enforce for a plugin call (ADR-0013)."""

    timeout_seconds: float
    max_output_bytes: int
    network: str = "brokered"  # no ambient network; egress only via the host's guard
    read_only_fs: bool = True
    run_as_non_root: bool = True

    @classmethod
    def from_manifest(cls, manifest: PluginManifest) -> SandboxSpec:
        return cls(
            timeout_seconds=manifest.limits.timeout_seconds,
            max_output_bytes=manifest.limits.max_output_bytes,
        )


class SandboxRunner(Protocol):
    async def run(
        self,
        connector: Connector,
        capability: str,
        args: dict[str, Any],
        ctx: ConnectorContext,
        spec: SandboxSpec,
    ) -> ConnectorResult: ...


class InProcessRunner:
    """Default runner. Enforces the wall-time limit; the "no ambient network" guarantee holds
    structurally because the connector is only ever handed an ``EgressGuard`` (not a socket).
    Deploy-profile runners (subprocess/container per ADR-0013) reinforce this with an OS boundary.
    """

    async def run(
        self,
        connector: Connector,
        capability: str,
        args: dict[str, Any],
        ctx: ConnectorContext,
        spec: SandboxSpec,
    ) -> ConnectorResult:
        try:
            return await asyncio.wait_for(
                connector.invoke(capability, args, ctx), timeout=spec.timeout_seconds
            )
        except TimeoutError:
            return ConnectorResult(ok=False, error="connector timed out")
