"""Network egress control (docs/14-Plugins/ConnectorStandards.md §5, PluginSecurity.md §1).

Connectors reach external systems **only** through this guard, which is **default-deny**: a URL
is allowed only if its scheme is https (or http where explicitly permitted), its host is on the
plugin's declared allowlist, and it does not resolve to a private/loopback/link-local address
(SSRF protection). In an **air-gapped** install, egress is globally disabled and every check
fails closed, so egress-dependent connectors are inert with no hidden phone-home.
"""

from __future__ import annotations

import ipaddress
import socket
from dataclasses import dataclass, field
from urllib.parse import urlparse


class EgressError(Exception):
    """Raised when an outbound request is not permitted (mapped to a connector failure)."""


@dataclass(frozen=True, slots=True)
class EgressPolicy:
    """Per-plugin egress policy: the allowlisted hosts and whether egress is enabled at all."""

    allowed_hosts: frozenset[str] = field(default_factory=frozenset)
    allow_http: bool = False  # https-only by default
    enabled: bool = True  # False in air-gapped installs → all egress denied


def _is_public_ip(host: str) -> bool:
    """Resolve host and require every address to be a global (non-private) unicast address."""
    try:
        infos = socket.getaddrinfo(host, None)
    except OSError:
        return False
    addrs = {info[4][0] for info in infos}
    if not addrs:
        return False
    for addr in addrs:
        try:
            ip = ipaddress.ip_address(addr)
        except ValueError:
            return False
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            return False
    return True


@dataclass(frozen=True, slots=True)
class EgressGuard:
    policy: EgressPolicy
    resolve: bool = True  # resolve + SSRF-check IPs; disabled only in fixture/offline tests

    def check(self, url: str) -> str:
        """Validate an outbound URL against the policy; return the host or raise ``EgressError``."""
        if not self.policy.enabled:
            raise EgressError("egress is disabled (air-gapped)")
        parsed = urlparse(url)
        scheme = parsed.scheme.lower()
        if scheme not in ("https", "http"):
            raise EgressError(f"scheme '{scheme}' not permitted")
        if scheme == "http" and not self.policy.allow_http:
            raise EgressError("http egress not permitted (https required)")
        host = parsed.hostname or ""
        if host.lower() not in self.policy.allowed_hosts:
            raise EgressError(f"host '{host}' is not on the egress allowlist")
        if self.resolve and not _is_public_ip(host):
            raise EgressError(f"host '{host}' resolves to a non-public address (SSRF blocked)")
        return host
