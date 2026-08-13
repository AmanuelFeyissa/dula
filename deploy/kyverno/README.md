# Kyverno admission policies (ADR-0015)

Cluster-scoped policies enforcing Dula's production admission controls. They apply to pods in
namespaces labelled `app.kubernetes.io/part-of: dula` (the Helm chart sets this label).

| Policy | Enforces |
|--------|----------|
| [require-pod-security.yaml](./require-pod-security.yaml) | non-root, read-only rootfs, drop ALL caps, seccomp RuntimeDefault, no privilege escalation, required CPU/memory limits |
| [verify-image-signatures.yaml](./verify-image-signatures.yaml) | only cosign-signed (keyed) Dula images may run — offline/air-gapped verifiable |

## Install

```bash
kubectl apply -f deploy/kyverno/          # after installing Kyverno itself
```

Before install, replace `COSIGN_PUBLIC_KEY_PLACEHOLDER_REPLACE_AT_INSTALL` in
`verify-image-signatures.yaml` with the mirrored release **public** key (the private signing key
stays in Vault/KMS, ADR-0015).

## Validation

- YAML well-formedness + basic shape are checked in CI (the `deploy` job).
- Full policy behaviour is validated with `kyverno test` / Chainsaw at deploy time (operational;
  the CLI is not bundled in PR CI).

See [../../docs/10-Security/SupplyChainSecurity.md](../../docs/10-Security/SupplyChainSecurity.md)
and [../../docs/11-Deployment/KubernetesDeployment.md](../../docs/11-Deployment/KubernetesDeployment.md).
