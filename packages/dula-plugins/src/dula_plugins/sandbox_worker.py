"""The plugin worker process (ADR-0013 baseline: out-of-process, host-brokered capabilities).

Runs one connector call in a fresh interpreter. The worker holds **no socket and no secret
value**: its HTTP goes through ``BrokerTransport``, which relays each request over the IPC pipe
to the host (the host runs it through the plugin's egress guard and its own network), and its
secrets are opaque ``$secret:<name>`` references that only the host resolves -- and only into
an outgoing request header, never back to the worker. On Linux the worker also drops into a
fresh user+network namespace before running, so even a bypass of the transport has nothing to
talk to; elsewhere that layer is absent (dev hosts, documented lower-assurance). A wall-time
kill and (POSIX) address-space rlimit bound what a runaway plugin can do.

Wire protocol (multiprocessing ``Connection``, picklable dicts):
    worker -> host  {"op": "http", "method", "url", "headers", "json"}
    host -> worker  {"op": "http_result", "status", "body"}
                    | {"op": "http_error", "kind", "message"}
    worker -> host  {"op": "result", "ok", "output", "error", "untrusted"}
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import os
import sys
from dataclasses import dataclass
from multiprocessing.connection import Connection
from typing import Any

import httpx

from dula_plugins.connector import Connector, ConnectorContext, ConnectorResult
from dula_plugins.egress import EgressError, EgressGuard, EgressPolicy
from dula_plugins.http import HttpError

SECRET_REF_PREFIX = "$secret:"  # noqa: S105 - a reference marker, not a secret


@dataclass(frozen=True, slots=True)
class BrokeredSecrets:
    """Hands out references, never values; the host substitutes them into request headers."""

    def get(self, key: str) -> str | None:
        return f"{SECRET_REF_PREFIX}{key}"


class BrokerTransport(httpx.AsyncBaseTransport):
    """An httpx transport that relays the request to the host instead of opening a socket."""

    def __init__(self, conn: Connection) -> None:
        self._conn = conn

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        body: Any = None
        if request.content:
            try:
                body = json.loads(request.content)
            except ValueError:
                body = request.content.decode("utf-8", errors="replace")
        msg = {
            "op": "http",
            "method": request.method,
            "url": str(request.url),
            "headers": dict(request.headers),
            "json": body,
        }
        reply = await asyncio.to_thread(self._roundtrip, msg)
        if reply.get("op") == "http_result":
            return httpx.Response(int(reply["status"]), content=bytes(reply["body"]))
        kind = reply.get("kind", "http")
        message = str(reply.get("message", "brokered request failed"))
        if kind == "egress":
            raise EgressError(message)
        raise HttpError(message)

    def _roundtrip(self, msg: dict[str, Any]) -> dict[str, Any]:
        self._conn.send(msg)
        reply = self._conn.recv()
        return reply if isinstance(reply, dict) else {"op": "http_error", "message": "bad reply"}


def _isolate(max_memory_bytes: int) -> None:
    """Best-effort OS hardening: no network namespace + address-space cap where available."""
    if sys.platform.startswith("linux"):
        # Unprivileged user namespaces may be disabled: then this degrades, but the brokered
        # network (no socket in the worker's hands) still holds.
        with contextlib.suppress(AttributeError, OSError):
            os.unshare(os.CLONE_NEWUSER | os.CLONE_NEWNET)  # type: ignore[attr-defined]
    with contextlib.suppress(ImportError, ValueError, OSError):
        import resource  # POSIX only

        limit = getattr(resource, "RLIMIT_AS", None)
        setrlimit = getattr(resource, "setrlimit", None)
        if limit is not None and setrlimit is not None:
            setrlimit(limit, (max_memory_bytes, max_memory_bytes))


def worker_main(
    conn: Connection,
    connector: Connector,
    capability: str,
    args: dict[str, Any],
    tenant: str,
    subject: str,
    policy: EgressPolicy,
    max_memory_bytes: int,
) -> None:
    _isolate(max_memory_bytes)
    ctx = ConnectorContext(
        tenant=tenant,
        subject=subject,
        # Same allowlist as the host applies again on its side: a local pre-check gives the
        # connector the same EgressError it would see in-process; the host check is the gate.
        egress=EgressGuard(policy=policy, resolve=False),
        secrets=BrokeredSecrets(),
        transport=BrokerTransport(conn),
    )
    try:
        result = asyncio.run(connector.invoke(capability, args, ctx))
    except Exception as exc:  # the host maps this to a failed, untrusted result
        result = ConnectorResult(ok=False, error=f"connector crashed: {type(exc).__name__}: {exc}")
    conn.send(
        {
            "op": "result",
            "ok": result.ok,
            "output": result.output,
            "error": result.error,
            "untrusted": result.untrusted,
        }
    )
    conn.close()
