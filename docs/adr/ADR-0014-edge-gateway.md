# ADR-0014: Edge / API Gateway Technology

- Status: Accepted
- Date: 2026-08-13
- Deciders: Architecture, Platform, Security
- Related: [ADR-0002](./ADR-0002-backend-language.md), [ADR-0009](./ADR-0009-auth-stack.md), [../03-Architecture/DeploymentArchitecture.md](../03-Architecture/DeploymentArchitecture.md), [../11-Deployment/KubernetesDeployment.md](../11-Deployment/KubernetesDeployment.md), [../01-Project/TechnologyStack.md](../01-Project/TechnologyStack.md)

## Context
The north-south **edge** (the entry point that terminates TLS and routes external traffic to the
web app and the APIs) was left **REQUIRES DECISION** — narrowed at M000 to *Envoy vs a FastAPI
edge* ([../PROJECT_REVIEW-M000.md](../PROJECT_REVIEW-M000.md) §9). Phase 09 (production) needs this
resolved to package a real ingress in the Helm chart.

Constraints that bound the choice:

- **Deploy anywhere incl. air-gapped/offline** (GuidingPrinciples §6) — no hosted/SaaS gateway, no
  phone-home; must run from a private registry.
- **Kubernetes-first** with Helm + Argo CD (§10.2); portable across cloud/on-prem/hybrid.
- **Security**: TLS termination, per-route rate limiting, request-size limits, header hygiene, and
  a clean seam for auth (OIDC/Keycloak, ADR-0009) — cross-cutting concerns kept **out** of app code.
- **Least moving parts**: reuse the accepted stack; do not adopt a heavy API-management platform we
  do not need.

Note: this is the **infrastructure edge**, distinct from the model-agnostic **LLM Gateway**
(ADR-0005), which is an application-layer concern and is unaffected.

## Options Considered
1. **FastAPI "edge" app** — a first-party FastAPI service as the public entry point. Reuses ADR-0002
   skills, but re-implements L7 concerns (routing, rate limiting, TLS, retries, circuit-breaking) in
   application code — exactly the cross-cutting logic a gateway should own — and becomes a bespoke,
   security-sensitive component we must harden ourselves. **Rejected** as the edge.
2. **ingress-nginx** — ubiquitous and simple, but configuration is annotation-driven and less
   expressive for typed routing/policy; the project is in maintenance mode. Viable, not preferred.
3. **Kong / APISIX** — full API-management platforms. Powerful, but bring a plugin ecosystem,
   control plane, and operational surface beyond our needs; heavier to run air-gapped. **Rejected**
   as over-scoped.
4. **Envoy Gateway implementing the Kubernetes Gateway API** — a CNCF Envoy-based controller that
   programs Envoy from the standard **Gateway API** CRDs (`Gateway`, `HTTPRoute`). Proven L7 data
   plane (TLS, routing, rate limiting, retries, mTLS upstream), portable and self-hosted, and the
   Gateway API is the vendor-neutral successor to Ingress.

## Decision
Adopt **Envoy Gateway, programmed via the Kubernetes Gateway API**, as the north-south edge for all
Kubernetes profiles; FastAPI services (ADR-0002) sit **behind** it and own only application logic.

- The edge terminates TLS (certs via **cert-manager**), routes to `web` and the APIs by host/path
  through `Gateway` + `HTTPRoute`, and applies **rate limiting, request-size limits, timeouts, and
  header hygiene** at the edge instead of in app code.
- **Authn/authz stay first-party**: tokens are verified in the services and authorization is via OPA
  (ADR-0009). The edge may later offload OIDC via an ext-auth hook, but the services remain
  fail-closed on their own (defence in depth) — the edge is not the sole authorization point.
- **Portability**: because routes are expressed in the standard **Gateway API**, another conformant
  implementation can be substituted per environment without changing app code or the route
  definitions — the Helm chart ships the Gateway API objects, and the controller is a values choice.
- **Air-gapped**: Envoy Gateway and Envoy run from mirrored images in a private registry with no
  external dependencies; nothing phones home.

The Helm umbrella chart (Phase 09) ships the `Gateway`/`HTTPRoute` objects behind a
`gateway.enabled` value; the local dev profile keeps using Docker Compose without the edge.

## Consequences
- **L7 concerns leave app code**: TLS, routing, rate limiting, and timeouts are declarative edge
  config, reducing bespoke security-sensitive code in the FastAPI services.
- **Standard, portable routing** via Gateway API; the controller is swappable per profile.
- **New runtime dependency** (Envoy Gateway controller + Envoy) in Kubernetes profiles — mitigated
  by it being CNCF, self-hosted, air-gappable, and only present in K8s (not local dev).
- **Learning/operational cost** of Gateway API CRDs; offset by it being the industry-standard
  direction and removing custom edge code.
- **Revisit** only if a profile mandates a specific managed gateway, or if Gateway API conformance
  regresses.

## Compliance / Verification
- The chart's Gateway API objects are schema-validated in CI (`kubeconform` with the Gateway API
  schemas) and `helm template` renders them under every profile; the air-gapped overlay asserts no
  external endpoints.
- Rate-limit/TLS/routing behaviour is validated at deploy time against a live gateway (operational,
  Phase 09 acceptance) — see [../11-Deployment/KubernetesDeployment.md](../11-Deployment/KubernetesDeployment.md).
