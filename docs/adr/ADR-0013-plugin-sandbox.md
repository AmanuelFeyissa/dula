# ADR-0013: Plugin Sandbox Mechanism

- Status: Accepted
- Date: 2026-08-13
- Deciders: Security, Architecture, Integrations
- Related: [ADR-0008](./ADR-0008-agent-runtime.md), [ADR-0009](./ADR-0009-auth-stack.md), [../03-Architecture/PluginArchitecture.md](../03-Architecture/PluginArchitecture.md), [../14-Plugins/PluginImplementation.md](../14-Plugins/PluginImplementation.md), [../10-Security/PluginSecurity.md](../10-Security/PluginSecurity.md)

## Context
Phase 07 delivered the plugin/connector framework with its **policy** controls (Ed25519 signing,
manifest least-privilege, OPA per-call authorization, default-deny egress + SSRF, resource limits,
untrusted output, revocation). The **isolation mechanism** — how a plugin's code is actually
contained so a compromised or malicious plugin cannot exceed those controls — was left
**REQUIRES DECISION** (container vs WASM vs subprocess; review C4/O3, M000).

Constraints that bound the choice:

- **Python-first SDK** (PluginFramework.md §3) — connectors are authored in Python today.
- **Deploy anywhere incl. air-gapped/offline** from one codebase (GuidingPrinciples §6) — the
  baseline must not require a container runtime or network to exist.
- **Defense-in-depth + least privilege** for a security product handling untrusted plugins.
- **Portability & reproducibility** across local dev, Docker, and Kubernetes.
- Must compose with the existing controls without becoming a *second* authorization surface.

## Options Considered
1. **In-process only** — plugins run inside the platform process. Simple, but a compromised plugin
   shares the host's memory, threads, sockets, and credentials. **Insufficient** as the boundary.
2. **WASM (WASI Preview 2 / component model)** — strong, deterministic, capability-based sandbox
   with no ambient authority — a near-perfect philosophical fit for the manifest/permission model.
   But **Python-in-WASM is immature**; adopting it as the *primary* mechanism would force the SDK to
   compiled languages (Rust/Go/AssemblyScript) and constrain connector authors today.
3. **Container / microVM per plugin** (rootless container, gVisor/Kata) — strong, well-understood,
   integrates with K8s network policy. But requires a **container runtime to exist**, so it cannot
   be the air-gapped/minimal/dev baseline; per-call spawn adds latency.
4. **Out-of-process worker (subprocess) with host-brokered capabilities** — the plugin runs in a
   separate OS process, hardened per platform, **with no ambient network, filesystem, or
   credentials**; the host brokers every capability (incl. all egress) over an IPC channel. Works
   everywhere Python runs, including air-gapped/dev, while giving a real process boundary.

## Decision
Adopt a **layered model** behind a single, pluggable **sandbox-runner interface** so the isolation
boundary is a deployment concern, not a code change:

- **Baseline (mandatory, all profiles incl. air-gapped/dev): out-of-process plugin worker
  (option 4).** Each plugin executes in a **separate process** that is **non-root**, has a
  **read-only root filesystem**, **no ambient credentials**, and **CPU/memory/wall-time/output
  limits**. Crucially the worker has **no ambient network** — it cannot open a socket; **all
  egress is brokered by the host** through the egress guard (ADR default-deny allowlist + SSRF).
  This yields WASM-like *capability-based* security (no ambient authority) with a Python SDK: even
  a fully compromised plugin can only do what the host hands it, capability by capability.
- **Hardening (where the OS supports it): Linux** workers run with **seccomp-bpf** (deny
  socket/exec/ptrace), **namespaces** (net = none, PID, mount, user), **cgroups** limits, and
  `no_new_privs`. On non-Linux **dev** hosts the baseline degrades to process + resource limits +
  brokered network (documented as lower-assurance, dev-only).
- **Defense-in-depth (orchestrated profiles): container/microVM per plugin.** In Docker/K8s the
  worker additionally runs in its **own rootless container** (**gVisor** recommended; Kata for
  hostile multi-tenant) with a **default-deny NetworkPolicy**. This *reinforces* the baseline; it
  does not replace it.
- **Future runner: WASM.** The runner interface admits a `WasmRunner` for compiled connectors where
  capability isolation and portability matter most — added without changing the host or the
  security controls. WASM is **not** the primary mechanism while the SDK is Python-first.

The framework already realizes the enforceable-in-process guarantees (timeout, output limit, and —
structurally — brokered-only network, since a connector receives an `EgressGuard`, never a raw
socket). Phase 07's host is refactored to run every call through a `SandboxRunner` (default
`InProcessRunner`); the `SubprocessRunner` (baseline worker) and `ContainerRunner` (deploy-profile)
implement the same interface and are delivered with the plugin worker/loader (Phase 07+/08).

## Consequences
- **Portable, air-gapped-first baseline**: the subprocess worker needs no container runtime and no
  network, so it runs in minimal/offline installs and local dev; stronger boundaries layer on where
  available. No single dependency is mandatory across all profiles.
- **Capability-based even in-process**: because the host brokers all egress, the "no ambient
  network" guarantee holds today via the `EgressGuard` seam — the process boundary and OS hardening
  strengthen it rather than introduce it.
- **Python SDK preserved**; connector authors are unaffected. A future `WasmRunner` is additive.
- **Cost**: per-call process (and, in orchestrated profiles, container) spawn adds latency; mitigated
  by worker pooling. Full seccomp/namespace hardening is Linux-specific; non-Linux dev is
  explicitly lower-assurance.
- **Revisit** only if the Python-first SDK is dropped (making WASM the natural primary) or a stronger
  default (microVM everywhere) becomes cheap and portable.

## Compliance / Verification
- The **policy controls** (signing, permissions, egress + SSRF, limits, untrusted output,
  revocation) are release-blocking and enforced **regardless of runner** (Phase 07 tests). The
  `SandboxRunner` seam is unit-tested (spec-from-manifest, timeout enforcement); worker/container
  runners add **sandbox-escape and egress-bypass tests** when delivered
  ([../15-Testing/SecurityTesting.md](../15-Testing/SecurityTesting.md)).
- Air-gapped behavior is preserved: egress disabled by default, egress-requiring capabilities inert,
  no phone-home ([../11-Deployment/AirGappedDeployment.md](../11-Deployment/AirGappedDeployment.md)).
