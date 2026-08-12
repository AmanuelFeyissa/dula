# deploy/

Packaging and deployment. One codebase, profiles via values overlays (ADR-0011,
[../docs/03-Architecture/DeploymentArchitecture.md](../docs/03-Architecture/DeploymentArchitecture.md)).

- `docker/` — Dockerfiles + `docker-compose.dev.yml` (local dev stack) *(Phase 01)*
- `helm/` — Helm charts (umbrella + per-component) *(Phase 01+)*
- `k8s/` — base manifests / kustomize overlays *(Phase 09)*
- `terraform/` — IaC for cloud/on-prem primitives *(Phase 09)*
