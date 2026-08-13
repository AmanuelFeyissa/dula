# ADR-0015: Supply-Chain & Release Integrity

- Status: Accepted
- Date: 2026-08-13
- Deciders: Security, Platform, Architecture
- Related: [ADR-0010](./ADR-0010-mlops-tooling.md), [ADR-0012](./ADR-0012-training-and-hosting.md), [ADR-0013](./ADR-0013-plugin-sandbox.md), [../10-Security/SupplyChainSecurity.md](../10-Security/SupplyChainSecurity.md), [../11-Deployment/KubernetesDeployment.md](../11-Deployment/KubernetesDeployment.md)

## Context
Phase 09 (production/GA) requires a **signed, reproducible release** with verifiable provenance,
deployable to every profile including air-gapped. Three related items were open: the **admission-
control tool** for image verification (**REQUIRES DECISION**, KubernetesDeployment.md §3), the
**SLSA target level** (**REQUIRES RESEARCH**), and **signed-commit enforcement** (**REQUIRES
DECISION**, RepositoryGovernance.md). This ADR settles all three as one coherent release-integrity
posture.

Constraints:

- **Air-gapped/offline first** — verification must work with **no external services** (no calls to
  a public transparency log or OIDC issuer at deploy time); keys and materials mirror into the
  private registry/cluster.
- **Reproducible & minimal** — pin by digest; keep the toolchain in the accepted stack.
- **Defence in depth** — signing + SBOM + scanning + admission enforcement, each independently
  valuable.

## Options Considered
- **Signing**: cosign **keyless** (Fulcio/Rekor + OIDC) vs cosign **keyed** (a private key held in
  KMS/Vault). Keyless is excellent in connected CI but **requires online Sigstore infrastructure**,
  which breaks air-gapped verification. Keyed signing verifies offline against a mirrored public key.
- **Admission control**: **Kyverno** vs Sigstore **policy-controller** vs OPA/Gatekeeper. All can
  verify signatures; policy-controller is signature-specific, Gatekeeper overlaps with our OPA use
  but is Rego-for-admission, and Kyverno additionally expresses the broader **pod-security** rules
  (non-root, read-only rootfs, resource limits, default-deny) we need in **one** YAML-native tool.
- **SLSA level**: L1 (provenance exists) … L3 (hardened, non-falsifiable build) … L4 (hermetic,
  two-party). L3 is the pragmatic production target on GitHub-hosted builders (ADR-0012).
- **Signed commits**: none / recommended / hard-enforced on protected branches.

## Decision
1. **Image signing — cosign, keyed.** Every release image is signed with a **private key held in
   Vault/KMS** (not keyless), so verification needs only the **mirrored public key** and works
   air-gapped. Signatures and attestations are stored as OCI artifacts alongside the image and
   mirrored with it.
2. **SBOM + provenance.** Generate a **CycloneDX/SPDX SBOM** per image with **syft**, and a build
   **provenance attestation** targeting **SLSA Build Level 3** (GitHub-hosted, isolated, signed
   provenance). Both are attached as cosign attestations.
3. **Vulnerability gate.** Scan images with **grype** (or Trivy) in the release pipeline and **fail
   on fixable High/Critical**; IaC/manifests scanned with a config scanner. These gate the release,
   not every PR (keeps PR CI fast).
4. **Admission control — Kyverno.** The cluster runs **Kyverno** policies that (a) **verifyImages**
   against the mirrored cosign public key (only signed, attested images run), and (b) enforce the
   pod-security baseline — **run-as-non-root, read-only root filesystem, drop ALL capabilities,
   seccomp RuntimeDefault, required resource limits, and default-deny** posture. Policies ship in
   `deploy/kyverno/` and are unit-tested in CI.
5. **Digest pinning.** Production values reference images by **immutable digest**, not tag.
6. **Signed commits — recommended now, enforced on protected branches at GA.** Contributors are
   encouraged to sign commits (Sigstore **gitsign** or GPG); enforcement on protected branches is
   turned on at GA to avoid mid-development friction. CI already blocks secrets (gitleaks) and runs
   the license/scan gates (Dependencies.md, SupplyChainSecurity.md).

## Consequences
- **Air-gapped-verifiable integrity**: keyed cosign + mirrored public key + Kyverno verifyImages
  means a disconnected cluster still refuses unsigned/tampered images — no Sigstore online
  dependency.
- **One admission tool** (Kyverno) covers both signature verification and pod-security, reducing
  operational surface versus running policy-controller *and* a separate PSP/Gatekeeper.
- **Key management burden**: a private signing key must be protected/rotated in Vault/KMS (the
  trade for offline verification); documented in SupplyChainSecurity.md.
- **SLSA L3, not L4**: hermetic/two-party (L4) is out of scope for GitHub-hosted builders now;
  L3 is the target and is revisited if a hermetic builder becomes available.
- **Release pipeline cost**: SBOM + scan + sign add time to the release workflow (not PR CI).
- **Revisit** if the project moves to a connected-only deployment model (keyless becomes viable) or
  adopts a hermetic build system (SLSA L4).

## Compliance / Verification
- **CI (per PR)**: Kyverno policies are unit-tested; Helm renders reference images and apply the
  security context the policies require; `kubeconform` validates manifests. Secret scan (gitleaks)
  and dependency/license gates run as today.
- **Release pipeline**: build → **syft** SBOM → **grype** gate (fail on fixable High/Critical) →
  **cosign** sign + attest (SBOM + SLSA provenance) → push by digest. Documented in
  [../10-Security/SupplyChainSecurity.md](../10-Security/SupplyChainSecurity.md).
- **At deploy**: Kyverno admission blocks any image lacking a valid signature/attestation; the
  air-gapped overlay is asserted to add no external endpoints.
