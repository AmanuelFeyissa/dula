"""Plugin host (docs/14-Plugins/PluginFramework.md §2, PluginLifecycle.md).

The host mediates **every** connector call. Lifecycle: install (verify Ed25519 signature +
validated manifest) → enable (capabilities become invokable) → disable / **revoke** (fleet-wide
kill for a compromised plugin). On invoke it enforces, in order: the plugin is enabled → the
caller is authorized for the capability's permission (OPA) → the call runs with a scoped egress
guard (default-deny allowlist; disabled when air-gapped) and a timeout; the result is returned as
**untrusted**. Every call is audited. The host cannot exceed the manifest, and neither can a
plugin (least privilege).
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Protocol

from dula_plugins.connector import Connector, ConnectorContext, ConnectorResult, SecretProvider
from dula_plugins.egress import EgressGuard, EgressPolicy
from dula_plugins.manifest import Capability, PluginManifest
from dula_plugins.signing import SignedPlugin, TrustStore, verify_plugin


class PluginState(StrEnum):
    INSTALLED = "installed"
    ENABLED = "enabled"
    DISABLED = "disabled"
    REVOKED = "revoked"  # terminal — a revoked plugin can never be re-enabled


class PermissionChecker(Protocol):
    """Structural port: authorize a capability action for a caller (OPA-backed in the service)."""

    async def check(
        self, *, action: str, tenant: str, subject: str, roles: Sequence[str]
    ) -> bool: ...


AuditHook = Callable[[dict[str, Any]], Awaitable[None]]


class HostError(Exception):
    """Raised for host-level failures (unknown/disabled plugin, capability, authz)."""


@dataclass
class InstalledPlugin:
    signed: SignedPlugin
    connector: Connector
    state: PluginState = PluginState.INSTALLED

    @property
    def manifest(self) -> PluginManifest:
        return self.signed.manifest


@dataclass
class PluginHost:
    trust: TrustStore
    checker: PermissionChecker
    secrets: SecretProvider
    egress_enabled: bool = True  # False in air-gapped installs → egress-dependent caps inert
    resolve_egress: bool = True  # SSRF DNS resolution (disabled in offline unit tests)
    audit: AuditHook | None = None
    _plugins: dict[str, InstalledPlugin] = field(default_factory=dict)

    def install(self, signed: SignedPlugin, connector: Connector) -> InstalledPlugin:
        """Verify the signature (Verify gate) and register the plugin as INSTALLED."""
        verify_plugin(signed, self.trust)  # raises SignatureError on failure
        if connector.manifest.id != signed.manifest.id:
            raise HostError("connector/manifest id mismatch")
        plugin = InstalledPlugin(signed=signed, connector=connector)
        self._plugins[signed.manifest.id] = plugin
        return plugin

    def enable(self, plugin_id: str) -> None:
        plugin = self._require(plugin_id)
        if plugin.state is PluginState.REVOKED:
            raise HostError(f"plugin '{plugin_id}' is revoked and cannot be enabled")
        plugin.state = PluginState.ENABLED

    def disable(self, plugin_id: str) -> None:
        self._require(plugin_id).state = PluginState.DISABLED

    def revoke(self, plugin_id: str) -> None:
        """Fleet-wide kill for a compromised plugin (terminal)."""
        self._require(plugin_id).state = PluginState.REVOKED

    def installed(self) -> list[InstalledPlugin]:
        return list(self._plugins.values())

    def connector(self, plugin_id: str) -> Connector | None:
        plugin = self._plugins.get(plugin_id)
        return plugin.connector if plugin is not None else None

    def find_capability(self, capability: str) -> tuple[InstalledPlugin, Capability] | None:
        for plugin in self._plugins.values():
            cap = plugin.manifest.capability(capability)
            if cap is not None:
                return plugin, cap
        return None

    async def invoke(
        self,
        capability: str,
        args: dict[str, Any],
        *,
        tenant: str,
        subject: str,
        roles: Sequence[str],
    ) -> ConnectorResult:
        found = self.find_capability(capability)
        if found is None:
            raise HostError(f"unknown capability '{capability}'")
        plugin, cap = found
        if plugin.state is not PluginState.ENABLED:
            raise HostError(f"plugin '{plugin.manifest.id}' is not enabled ({plugin.state.value})")

        allowed = await self.checker.check(
            action=cap.permission, tenant=tenant, subject=subject, roles=roles
        )
        await self._emit(capability, tenant, subject, "permission", {"allowed": allowed})
        if not allowed:
            raise HostError(f"not authorized for capability '{capability}' ({cap.permission})")

        ctx = ConnectorContext(
            tenant=tenant,
            subject=subject,
            egress=self._egress_for(plugin.manifest),
            secrets=self.secrets,
        )
        try:
            result = await asyncio.wait_for(
                plugin.connector.invoke(capability, args, ctx),
                timeout=plugin.manifest.limits.timeout_seconds,
            )
        except TimeoutError:
            result = ConnectorResult(ok=False, error="connector timed out")
        await self._emit(capability, tenant, subject, "invoked", {"ok": result.ok})
        return result

    def _egress_for(self, manifest: PluginManifest) -> EgressGuard:
        policy = EgressPolicy(
            allowed_hosts=frozenset(h.lower() for h in manifest.egress),
            enabled=self.egress_enabled,
        )
        return EgressGuard(policy=policy, resolve=self.resolve_egress)

    def _require(self, plugin_id: str) -> InstalledPlugin:
        plugin = self._plugins.get(plugin_id)
        if plugin is None:
            raise HostError(f"unknown plugin '{plugin_id}'")
        return plugin

    async def _emit(
        self, capability: str, tenant: str, subject: str, kind: str, detail: dict[str, Any]
    ) -> None:
        if self.audit is None:
            return
        await self.audit(
            {"capability": capability, "tenant": tenant, "subject": subject, "kind": kind, **detail}
        )
