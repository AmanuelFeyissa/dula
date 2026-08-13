# deploy/

Packaging and deployment. One codebase, profiles via values overlays (ADR-0011,
[../docs/03-Architecture/DeploymentArchitecture.md](../docs/03-Architecture/DeploymentArchitecture.md)).

- `docker/` — Dockerfiles + `docker-compose.dev.yml` (local dev stack) *(Phase 01)*
- `helm/dula/` — **umbrella Helm chart** + per-profile values overlays (cloud/onprem/hybrid/airgapped) *(Phase 09, CURRENT)*
- `kyverno/` — admission policies: image-signature verification + pod-security baseline (ADR-0015) *(Phase 09)*
- `airgap/` — offline image bundle (`images.txt`, `mirror-images.sh`) + `verify-airgap.sh` no-egress assertion *(Phase 09)*
- `observability/` — Prometheus rules + Grafana dashboard *(Phase 09)*
- `backup/` — Postgres backup/restore scripts for DR drills *(Phase 09)*
- `opa/` — authorization policy + tests *(Phase 01+)*
- `argo/` — Argo Workflows (Dula AI training) *(Phase 04)*
- `terraform/` — IaC for cloud/on-prem primitives *(Phase 09+, FUTURE)*

**One chart, all profiles** — differences are values overlays, not code
(ADR-0011/0014/0015). Validate locally:

```bash
helm lint deploy/helm/dula
helm template dula deploy/helm/dula -f deploy/helm/dula/values-airgapped.yaml
bash deploy/airgap/verify-airgap.sh          # air-gapped no-egress assertion
```

See [../docs/11-Deployment/KubernetesDeployment.md](../docs/11-Deployment/KubernetesDeployment.md)
and [../docs/11-Deployment/GAReadiness.md](../docs/11-Deployment/GAReadiness.md).
