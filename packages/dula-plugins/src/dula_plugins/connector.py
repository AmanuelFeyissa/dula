"""Connector contract (docs/14-Plugins/ConnectorStandards.md §2).

A connector adapts an external system into typed capabilities. It receives a `ConnectorContext`
carrying the tenant/subject, the **egress guard** (its only path to the network), and a scoped
**secret provider** — it can never reach beyond what the host grants. Every result is marked
**untrusted**: connector output is external, validated evidence, never trusted commands.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from dula_plugins.egress import EgressGuard
from dula_plugins.manifest import PluginManifest


class SecretProvider(Protocol):
    """Scoped secret access (Vault-backed in prod; in-memory offline). Never logged."""

    def get(self, key: str) -> str | None: ...


@dataclass
class InMemorySecrets:
    _secrets: dict[str, str] = field(default_factory=dict)

    def get(self, key: str) -> str | None:
        return self._secrets.get(key)


@dataclass(frozen=True, slots=True)
class ConnectorContext:
    tenant: str
    subject: str
    egress: EgressGuard
    secrets: SecretProvider


@dataclass(frozen=True, slots=True)
class ConnectorResult:
    ok: bool
    output: Any = None
    error: str | None = None
    untrusted: bool = True


@runtime_checkable
class Connector(Protocol):
    manifest: PluginManifest

    async def invoke(
        self, capability: str, args: dict[str, Any], ctx: ConnectorContext
    ) -> ConnectorResult: ...
