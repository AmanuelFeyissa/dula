"""Dula plugin/connector framework (Phase 07 — docs/03-Architecture/PluginArchitecture.md).

Connects Dula to the external security ecosystem (SIEM, EDR, TI, ticketing) through **signed,
sandboxed connectors**. The design stance is that **plugins are untrusted by default — even
first-party** (docs/14-Plugins/PluginSecurity.md): the host verifies an Ed25519 signature over
the manifest before install, grants only manifest-declared permissions on enable, forces all
network egress through a **default-deny allowlist with SSRF protection**, bounds resources, and
treats every connector output as untrusted evidence.

Everything runs **offline** by default: built-in connectors are backed by in-memory fixtures so
contract tests need no live external calls, and any connector that *requires* egress is **inert
in an air-gapped install** unless egress is explicitly permitted (no hidden phone-home). The
process/WASM sandbox mechanism itself is still **REQUIRES DECISION**; this framework enforces the
*policy* controls (signing, permissions, egress, limits, untrusted output, revocation) that a
process/container boundary will later reinforce.
"""

from __future__ import annotations
