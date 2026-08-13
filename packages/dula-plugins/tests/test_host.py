"""Tests for the plugin host: lifecycle, permission enforcement, invocation, revocation."""

from __future__ import annotations

from collections.abc import Callable

import pytest
from dula_plugins.builtin import BuiltinBackends
from dula_plugins.connectors.siem import SIEM_PLUGIN_ID, SiemSearchConnector, siem_manifest
from dula_plugins.host import HostError, PluginHost, PluginState
from dula_plugins.signing import SignatureError, TrustStore, generate_keypair, sign_manifest

HostFactory = Callable[..., tuple[PluginHost, BuiltinBackends]]


def test_builtin_plugins_installed_and_enabled(
    full_checker, backends: BuiltinBackends, host_factory: HostFactory
) -> None:
    host, _ = host_factory(full_checker, backends)
    installed = host.installed()
    assert {p.manifest.id for p in installed} == {
        "dula-plugin-dula-siem",
        "dula-plugin-dula-ti",
        "dula-plugin-dula-ticketing",
    }
    assert all(p.state is PluginState.ENABLED for p in installed)


async def test_invoke_read_capability_normalizes(
    full_checker, backends: BuiltinBackends, host_factory: HostFactory, tenant: str
) -> None:
    host, _ = host_factory(full_checker, backends)
    result = await host.invoke(
        "siem.search", {"query": "HOST-7"}, tenant=tenant, subject="u1", roles=["analyst"]
    )
    assert result.ok and result.untrusted is True
    assert result.output["count"] == 2
    assert result.output["events"][0]["source"] == "siem"


async def test_permission_denied_raises(
    checker_factory: Callable[..., object],
    backends: BuiltinBackends,
    host_factory: HostFactory,
    tenant: str,
) -> None:
    host, _ = host_factory(checker_factory("connector.siem.search"), backends)
    with pytest.raises(HostError, match="not authorized"):
        await host.invoke(
            "siem.search", {"query": "x"}, tenant=tenant, subject="u1", roles=["analyst"]
        )


async def test_disabled_plugin_cannot_be_invoked(
    full_checker, backends: BuiltinBackends, host_factory: HostFactory, tenant: str
) -> None:
    host, _ = host_factory(full_checker, backends)
    host.disable(SIEM_PLUGIN_ID)
    with pytest.raises(HostError, match="not enabled"):
        await host.invoke(
            "siem.search", {"query": "x"}, tenant=tenant, subject="u1", roles=["analyst"]
        )


def test_revoked_plugin_cannot_be_reenabled(
    full_checker, backends: BuiltinBackends, host_factory: HostFactory
) -> None:
    host, _ = host_factory(full_checker, backends)
    host.revoke(SIEM_PLUGIN_ID)
    with pytest.raises(HostError, match="revoked"):
        host.enable(SIEM_PLUGIN_ID)


async def test_unknown_capability_raises(
    full_checker, backends: BuiltinBackends, host_factory: HostFactory, tenant: str
) -> None:
    host, _ = host_factory(full_checker, backends)
    with pytest.raises(HostError, match="unknown capability"):
        await host.invoke("siem.nope", {}, tenant=tenant, subject="u1", roles=["analyst"])


def test_install_rejects_untrusted_signature(full_checker) -> None:
    # A plugin signed by a key the host does not trust must not install.
    private, _public = generate_keypair()
    signed = sign_manifest(siem_manifest(), private)
    host = PluginHost(trust=TrustStore(), checker=full_checker, secrets=_NoSecrets())
    with pytest.raises(SignatureError):
        host.install(signed, SiemSearchConnector(_EmptyBackend()))


class _NoSecrets:
    def get(self, key: str) -> str | None:
        return None


class _EmptyBackend:
    async def query(self, tenant: str, query: str, limit: int):
        return []
