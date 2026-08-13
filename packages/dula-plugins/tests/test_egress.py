"""Tests for the egress allowlist + SSRF guard (default-deny)."""

from __future__ import annotations

import pytest
from dula_plugins.egress import EgressError, EgressGuard, EgressPolicy


def _guard(hosts: set[str], *, enabled: bool = True, resolve: bool = False, http: bool = False):
    return EgressGuard(
        policy=EgressPolicy(allowed_hosts=frozenset(hosts), enabled=enabled, allow_http=http),
        resolve=resolve,
    )


def test_allowed_https_host_passes() -> None:
    guard = _guard({"ti.example.com"})
    assert guard.check("https://ti.example.com/api?x=1") == "ti.example.com"


def test_host_not_on_allowlist_denied() -> None:
    with pytest.raises(EgressError, match="allowlist"):
        _guard({"ti.example.com"}).check("https://evil.example.net/steal")


def test_non_http_scheme_denied() -> None:
    with pytest.raises(EgressError, match="scheme"):
        _guard({"ti.example.com"}).check("file:///etc/passwd")


def test_http_denied_unless_permitted() -> None:
    with pytest.raises(EgressError, match="http"):
        _guard({"ti.example.com"}).check("http://ti.example.com/x")
    # Permitted when explicitly allowed.
    assert (
        _guard({"ti.example.com"}, http=True).check("http://ti.example.com/x") == "ti.example.com"
    )


def test_egress_disabled_denies_everything() -> None:
    with pytest.raises(EgressError, match="disabled"):
        _guard({"ti.example.com"}, enabled=False).check("https://ti.example.com/x")


def test_ssrf_loopback_blocked_when_resolving() -> None:
    # localhost is on the allowlist but resolves to a loopback address → SSRF blocked.
    with pytest.raises(EgressError, match=r"SSRF|non-public"):
        _guard({"localhost"}, resolve=True).check("https://localhost/admin")


def test_ssrf_unresolvable_host_blocked() -> None:
    with pytest.raises(EgressError, match=r"SSRF|non-public"):
        _guard({"nonexistent.invalid"}, resolve=True).check("https://nonexistent.invalid/x")
