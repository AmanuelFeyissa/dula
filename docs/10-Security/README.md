---
title: Security — Overview
document_id: SEC-000
status: Draft
version: 0.1.0
last_updated: 2026-08-11
owner: Security
audience: All engineers, security team
phase: Documentation Bootstrap (M000)
---

# 10 — Security

> **Purpose.** The security area defines how Dula is threat-modeled, built, and defended.
> For a cybersecurity product handling highly sensitive data, security is a first-class
> constraint, not a feature.

## Documents

- [ThreatModel.md](./ThreatModel.md) — platform threat model.
- [AIThreatModel.md](./AIThreatModel.md) — AI/LLM-specific threats (injection, poisoning…).
- [SecureDevelopment.md](./SecureDevelopment.md) — secure SDLC.
- [AgentSecurity.md](./AgentSecurity.md) — agent-specific controls.
- [PluginSecurity.md](./PluginSecurity.md) — plugin/connector sandboxing.
- [DataSecurity.md](./DataSecurity.md) — data protection, secrets, encryption.
- [SupplyChainSecurity.md](./SupplyChainSecurity.md) — build/dependency integrity.
- [SecurityTesting.md](./SecurityTesting.md) — security testing program.

## Foundations

- Architecture view: [../03-Architecture/SecurityArchitecture.md](../03-Architecture/SecurityArchitecture.md).
- Principles: [../02-Vision/GuidingPrinciples.md](../02-Vision/GuidingPrinciples.md)
  (defensive-only, data sovereignty, human-in-command).

## Cross-Cutting Rules

1. Treat **all** model output and retrieved/plugin content as **untrusted**.
2. Enforce authZ at the service layer and at retrieval, not only the UI.
3. Least privilege for every service, agent, and plugin; default-deny egress.
4. Everything sensitive is encrypted, secret-managed, and audited.
