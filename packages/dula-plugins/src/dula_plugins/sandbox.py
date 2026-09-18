"""Sandbox runner (ADR-0013 — plugin sandbox mechanism).

The isolation boundary is a **pluggable seam**, so it can be strengthened per deployment profile
without changing the host or the security controls. A `SandboxSpec` (derived from the manifest)
declares the guarantees a runner must uphold: wall-time/output limits, **no ambient network**
(egress is brokered by the host — the connector only ever holds an `EgressGuard`, never a raw
socket), read-only filesystem, and non-root execution.

- `InProcessRunner` (default, all profiles incl. air-gapped/dev): enforces the guarantees that are
  enforceable in-process — the timeout, and structurally the brokered-only network. It is the
  baseline the other runners strengthen.
- `SubprocessRunner` (the ADR-0013 baseline): each call runs in a **fresh interpreter** that
  holds no socket and no secret value -- HTTP is relayed to the host, which applies the egress
  guard and substitutes secrets into headers; on Linux the worker also sits in an empty network
  namespace; a wall-time kill and an address-space rlimit bound it (see ``sandbox_worker``).
- `ContainerRunner` (orchestrated profiles, gVisor/Kata) reinforces that with a container boundary
  and is FUTURE, as is a `WasmRunner`; both slot into the same interface.
"""

from __future__ import annotations

import asyncio
import multiprocessing as mp
from dataclasses import dataclass
from typing import Any, Protocol

import httpx

from dula_plugins.connector import Connector, ConnectorContext, ConnectorResult
from dula_plugins.egress import EgressError
from dula_plugins.http import EgressHttpClient, HttpError
from dula_plugins.manifest import PluginManifest


@dataclass(frozen=True, slots=True)
class SandboxSpec:
    """The isolation guarantees a runner must enforce for a plugin call (ADR-0013)."""

    timeout_seconds: float
    max_output_bytes: int
    max_memory_bytes: int = 512 * 1024 * 1024
    network: str = "brokered"  # no ambient network; egress only via the host's guard
    read_only_fs: bool = True
    run_as_non_root: bool = True

    @classmethod
    def from_manifest(cls, manifest: PluginManifest) -> SandboxSpec:
        return cls(
            timeout_seconds=manifest.limits.timeout_seconds,
            max_output_bytes=manifest.limits.max_output_bytes,
            max_memory_bytes=manifest.limits.max_memory_bytes,
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


class SubprocessRunner:
    """ADR-0013 baseline: the call runs in a separate process; the host brokers its capabilities.

    The connector object is pickled into a spawned interpreter (so it must be picklable -- the
    built-ins are; a fixture backend's in-memory state is copied, not shared). While the call
    runs, the host services the worker's HTTP requests: each one is checked against the
    plugin's egress guard *here*, secret references in headers are resolved *here*, and the
    response body goes back over the pipe. The worker is killed at the wall-time limit.
    ``transport`` is a test seam for the host-side client only.
    """

    def __init__(self, *, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self._transport = transport

    async def run(
        self,
        connector: Connector,
        capability: str,
        args: dict[str, Any],
        ctx: ConnectorContext,
        spec: SandboxSpec,
    ) -> ConnectorResult:
        from dula_plugins.sandbox_worker import worker_main

        mp_ctx = mp.get_context("spawn")
        host_conn, worker_conn = mp_ctx.Pipe(duplex=True)
        proc = mp_ctx.Process(
            target=worker_main,
            args=(
                worker_conn,
                connector,
                capability,
                args,
                ctx.tenant,
                ctx.subject,
                ctx.egress.policy,
                spec.max_memory_bytes,
            ),
            daemon=True,
        )
        proc.start()
        worker_conn.close()
        try:
            return await asyncio.wait_for(
                self._serve(host_conn, ctx, spec), timeout=spec.timeout_seconds
            )
        except TimeoutError:
            return ConnectorResult(ok=False, error="connector timed out")
        finally:
            if proc.is_alive():
                proc.kill()
            host_conn.close()
            await asyncio.to_thread(proc.join, 5)

    async def _serve(self, conn: Any, ctx: ConnectorContext, spec: SandboxSpec) -> ConnectorResult:
        # ``conn`` is a multiprocessing Connection (PipeConnection on Windows).
        while True:
            try:
                msg = await asyncio.to_thread(conn.recv)
            except (EOFError, OSError):
                return ConnectorResult(ok=False, error="connector worker exited without a result")
            if not isinstance(msg, dict):
                return ConnectorResult(ok=False, error="connector worker sent a malformed message")
            op = msg.get("op")
            if op == "result":
                return ConnectorResult(
                    ok=bool(msg.get("ok")),
                    output=msg.get("output"),
                    error=msg.get("error"),
                    untrusted=True,
                )
            if op == "http":
                conn.send(await self._brokered_http(msg, ctx, spec))
                continue
            return ConnectorResult(ok=False, error=f"connector worker sent unknown op {op!r}")

    async def _brokered_http(
        self, msg: dict[str, Any], ctx: ConnectorContext, spec: SandboxSpec
    ) -> dict[str, Any]:
        from dula_plugins.sandbox_worker import SECRET_REF_PREFIX

        headers: dict[str, str] = {}
        for name, value in dict(msg.get("headers") or {}).items():
            if isinstance(value, str) and value.startswith(SECRET_REF_PREFIX):
                real = ctx.secrets.get(value[len(SECRET_REF_PREFIX) :])
                if real is None:
                    continue  # unknown secret: header dropped, never a reference leak
                value = real
            headers[str(name)] = str(value)
        headers.pop("content-length", None)  # httpx recomputes it for the re-encoded body
        client = EgressHttpClient(
            ctx.egress,
            timeout_seconds=spec.timeout_seconds,
            max_response_bytes=spec.max_output_bytes,
            transport=self._transport,
        )
        try:
            resp = await client.request(
                str(msg.get("method", "GET")),
                str(msg.get("url", "")),
                headers=headers,
                json_body=msg.get("json"),
            )
        except EgressError as exc:
            return {"op": "http_error", "kind": "egress", "message": str(exc)}
        except HttpError as exc:
            return {"op": "http_error", "kind": "http", "message": str(exc)}
        return {"op": "http_result", "status": resp.status, "body": resp.body}
