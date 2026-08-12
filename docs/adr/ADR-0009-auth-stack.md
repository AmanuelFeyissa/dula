# ADR-0009: Authentication & Authorization Stack

- Status: Accepted
- Date: 2026-08-11
- Deciders: Security, Architecture
- Related: [../12-API/Authentication.md](../12-API/Authentication.md), [../12-API/Authorization.md](../12-API/Authorization.md)

## Context
Enterprise/air-gapped identity + fine-grained, consistent authorization across services.

## Options Considered
- IdP: **Keycloak** (mature, self-hostable OIDC/SAML, MFA, federation) vs Ory/Authentik
  (lighter) vs Auth0 (SaaS — excluded, conflicts with air-gapped).
- Policy: **OPA/Rego** (externalized RBAC+ABAC) vs Cedar/Casbin vs app-native.

## Decision
- **Keycloak (OIDC/OAuth2) for authentication** — self-hosted, air-gap capable, federation.
- **OPA/Rego for authorization** — RBAC + ABAC, enforced at the service layer **and at RAG
  retrieval**, tenant-scoped.
- Short-lived JWTs; mTLS/workload identity between services.

## Consequences
- Consistent, testable authz; no SaaS dependency. Operational cost of running Keycloak+OPA
  accepted.

## Compliance / Verification
- Rego policy unit tests + tenant-isolation integration tests are release-blocking.
