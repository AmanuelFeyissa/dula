---
title: Authentication
document_id: API-002
status: Draft
version: 0.1.0
last_updated: 2026-08-11
owner: Security / Backend
audience: Backend & security engineers
phase: Documentation Bootstrap (M000)
related:
  - ./Authorization.md
  - ../03-Architecture/SecurityArchitecture.md
---

# Authentication

> **Purpose.** Define how identities are established for humans and services (ADR-0009).

## 1. Human Authentication

- **Keycloak** as the IdP: OIDC/OAuth2, MFA, and federation to enterprise IdPs (SAML/OIDC).
- Clients receive short-lived **JWT access tokens** + refresh tokens; tokens carry
  identity, tenant, and roles (consumed by authZ — [./Authorization.md](./Authorization.md)).

## 2. Service Authentication

- Workload identity + **mTLS** between services; no implicit trust
  ([../03-Architecture/SecurityArchitecture.md](../03-Architecture/SecurityArchitecture.md)).

## 3. Token Handling

- Short lifetimes; rotation/refresh; revocation supported; tokens validated at the gateway
  and services (signature, expiry, audience, tenant).

## 4. API Keys / Programmatic Access

- Scoped, revocable API credentials for integrations/automation; least privilege; stored
  as secrets (Vault), never logged.

## 5. Air-Gapped

- Keycloak runs on-prem; no external IdP required. Optional federation only if the
  customer provides an internal IdP.

## 6. Auditing

- All authentication events audited ([../10-Security/DataSecurity.md](../10-Security/DataSecurity.md)).

## 7. Open Decisions

- ADR-0009 finalizes Keycloak vs alternatives (Ory/Authentik) and token lifetimes.
