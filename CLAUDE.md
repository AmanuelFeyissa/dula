# CLAUDE.md

This file is the permanent operating contract for Claude Code when working in this repository.

It defines how Claude Code must understand, modify, document, test, secure, and advance the Dula project.

The repository itself is the source of truth. Conversation history is temporary and must never be treated as the project's durable memory.

---

# 1. What This Repository Is

Dula is a cybersecurity AI ecosystem consisting of two independently deployable products:

- **Dula** — the Cybersecurity AI Platform (Product 1) and the name of the overall ecosystem. Use **Dula Platform** when disambiguating Product 1 specifically.
- **Dula AI** — the cybersecurity-specialized LLM (Product 2).

The name Dula comes from Oromo (*Duulaa* = warrior/knight; *Abbaa Duulaa* = war leader/defense commander).

## Naming rule

Never reintroduce the old placeholder names:

- `Aegis`
- `SecLLM`

Use:

- `Dula`
- `Dula Platform`
- `Dula AI`

Model artifacts use the `dula-` prefix (e.g. `dula-<base>-<task>-<method>-vX.Y`).

---

# 2. Project Mission

Dula is intended to become a serious cybersecurity AI ecosystem capable of assisting security teams with:

- Security Operations
- SOC operations
- Threat detection
- Threat hunting
- Incident response
- Threat intelligence
- Vulnerability analysis
- Security log analysis
- Detection engineering
- Malware analysis assistance
- Digital forensics assistance
- Cloud security
- Kubernetes security
- Security investigation
- Security automation
- Security reporting
- Security knowledge management
- AI agents
- Security tool integrations

The long-term platform must support:

- Local development
- Docker
- Kubernetes
- Cloud
- On-premises
- Hybrid
- Air-gapped environments
- Offline model deployment

These deployment profiles are **first-class from one codebase and chart set**; profiles vary by environment through configuration/Helm value overlays, not code forks (see `docs/02-Vision/GuidingPrinciples.md` §6 and `docs/03-Architecture/DeploymentArchitecture.md`).

---

# 3. Two-Product Architecture

## Product 1 — Dula Platform

The Dula Platform is the application, orchestration, integration, security, and operational layer.

It is responsible for capabilities including:

- Authentication
- Authorization
- RBAC
- Multi-tenancy
- APIs
- LLM Gateway
- Model management
- RAG
- Knowledge management
- Search
- Threat intelligence
- Security analytics
- Agent orchestration
- Plugin/connector framework
- Workflow automation
- Audit logging
- Observability
- Configuration
- Integrations
- Security controls
- Deployment
- Operations

## Product 2 — Dula AI

Dula AI is the cybersecurity-specialized intelligence layer.

It should progressively support:

- Cybersecurity question answering
- Security log analysis
- IOC analysis
- Threat intelligence analysis
- CVE analysis
- MITRE ATT&CK mapping
- Detection engineering
- Sigma generation
- YARA generation
- Security investigation
- Incident analysis
- Malware-analysis assistance
- Threat-hunting assistance
- Vulnerability analysis
- Cloud security analysis
- Kubernetes security analysis
- Security report generation
- Tool calling
- Agentic workflows

Dula AI must remain separable from the platform.

The platform must not become permanently dependent on one model implementation. All model access goes through the model-agnostic **LLM Gateway** (see `docs/03-Architecture/AIArchitecture.md`).

---

# 4. Current Project State

Current stage:

**Documentation Bootstrap — M000**

The repository currently contains documentation and project-definition artifacts. The M000 architecture & documentation review is **complete**, and **ADR-0001…0010 are Accepted** (see `docs/PROJECT_REVIEW-M000.md`, `docs/adr/`, and `docs/PROJECT_STATE.md`).

Unless the repository explicitly shows otherwise, assume:

- No production application exists.
- No production infrastructure exists.
- No trained Dula AI model exists.
- No production datasets exist.
- No production deployment exists.
- No CI/CD pipeline exists.
- No application build/lint/test toolchain exists.

Do not invent commands for infrastructure that does not exist.

Implementation begins at:

**M001 / Phase 01**

Implementation must not begin unless explicitly directed or the current milestone's instructions authorize it.

Always keep `docs/PROJECT_STATE.md` current as work progresses; treat `docs/PROJECT_CONTEXT.md` as durable project knowledge to read first for context recovery.

---

# 5. Repository Structure

The current repository contains:

```text
README.md
CLAUDE.md

docs/
├── README.md
├── SUMMARY.md
├── PROJECT_CONTEXT.md
├── PROJECT_STATE.md
├── PROJECT_REVIEW-M000.md
│
├── 00-Governance/
├── 01-Project/
├── 02-Vision/
├── 03-Architecture/
├── 04-MVP-Roadmap/
├── 05-Backend/
├── 06-Frontend/
├── 07-Database/
├── 08-AI/
├── 09-MLOps/
├── 10-Security/
├── 11-Deployment/
├── 12-API/
├── 13-Agents/
├── 14-Plugins/
├── 15-Testing/
├── 16-Operations/
│
└── adr/
    ├── README.md
    ├── ADR-0001-product-naming.md
    ├── … (ADR-0002 … ADR-0009)
    └── ADR-0010-mlops-tooling.md
```

Start from `docs/README.md` (reading order) and `docs/SUMMARY.md` (full index). `docs/01-Project/ProjectStructure.md` describes the **planned** code layout (`apps/`, `services/`, `packages/`, `ml/`, `deploy/`), which does not exist yet.

---

# 6. Architecture Decisions Are Binding

The ten ADRs in `docs/adr/` are **Accepted** and constrain the design. Do not contradict them in edits. A changed decision requires a **new** ADR (`docs/adr/ADR-NNNN-title.md`, next sequential number, never reuse numbers) following `docs/00-Governance/ArchitectureDecisionRecords.md`. Superseded ADRs keep their number and status.

Accepted baselines a future instance must not casually re-litigate:

- **ADR-0001** — Naming: Dula / Dula AI.
- **ADR-0002** — Backend: Python 3.12 + FastAPI primary; **Go approved for high-throughput data-plane** components. Frontend: Next.js/React/TypeScript.
- **ADR-0003** — Vector store: **Qdrant**. Search/BM25 + log-analytics: **OpenSearch**. Hybrid = Qdrant + OpenSearch. (pgvector is not the platform vector store.)
- **ADR-0004** — Event & streaming backbone: **Redpanda (Kafka API)** — permanent (Apache Kafka is a drop-in equivalent).
- **ADR-0005** — Serving: vLLM (GPU) + llama.cpp (CPU/air-gapped) + Ollama (dev), behind the LLM Gateway.
- **ADR-0006** — Multi-tenancy: logical isolation (tenant_id + Postgres RLS + index namespacing) **plus mandatory AI-layer isolation** (no prompt/KV/response cache shared across tenants).
- **ADR-0007** — Base models: **Apache-2.0 families (Qwen/Mistral) preferred; Llama deprioritized** for licensing; final checkpoint chosen empirically by benchmark; verify model-weight provenance/hashes.
- **ADR-0008** — Agents: **built on LangGraph** with a first-party permission/approval/audit layer.
- **ADR-0009** — Auth: Keycloak (OIDC) + OPA (Rego).
- **ADR-0010** — MLOps: MLflow + DVC + Argo Workflows.

Repository model: **monorepo `dula`** (ADR-0011, Accepted).

- **ADR-0012** — Dula AI training compute & artifact hosting: GitHub (source/CI) + Hugging Face Hub (artifacts) + free GPU tiers (Kaggle/Lightning/Modal).
- **ADR-0013** — Plugin sandbox: **out-of-process worker with host-brokered capabilities** (no ambient network) as the portable baseline + rootless container (gVisor/Kata) per orchestrated profile, behind a pluggable sandbox-runner; WASM a future runner. The policy controls hold regardless of runner.
- **ADR-0014** — Edge / API gateway: **Envoy Gateway (Kubernetes Gateway API)** at the north-south edge (TLS, routing, rate limiting); FastAPI services behind it; authz/authn stay first-party (OPA/Keycloak). Air-gappable, no phone-home.
- **ADR-0015** — Supply-chain & release integrity: cosign **keyed** signing (offline-verifiable) + **syft** SBOM + **grype** scan gate + **Kyverno** admission (verify signatures + pod-security baseline); **SLSA Build L3**; signed commits recommended, enforced on protected branches at GA.
- **ADR-0016** — Agent & playbook run persistence: AI Gateway gains an **optional** Postgres dependency (`run_store: memory|postgres`, default `memory`) — `PostgresRunStore` behind the same async `RunStore` interface as `InMemoryRunStore`, own migration chain sharing platform-api's database but not its tables (no cross-service FK), RLS-scoped by tenant.

Still open (non-blocking, not yet ADRs): empirical items only — embedding/reranker model and training/inference hardware sizing (measured when the relevant phase arrives).

---

# 7. Cross-Cutting Principles

Keep these invariants consistent in every doc and (later) every implementation. They come from `docs/02-Vision/GuidingPrinciples.md`, `docs/03-Architecture/`, and `docs/10-Security/`:

- **Deploy-anywhere incl. air-gapped/offline** from one codebase — a capability that cannot degrade gracefully offline is not "done".
- **All model output and all retrieved/tool/plugin content is untrusted** (prompt-injection defense). The AI threat model maps to **OWASP Top 10 for LLM Applications : 2025** (`docs/10-Security/AIThreatModel.md`).
- **Evaluation gates everything** in the AI strategy — no model/prompt/RAG/agent change ships without measured, non-regressing quality **and** safety (`docs/08-AI/EvaluationStrategy.md`, `docs/09-MLOps/`).
- **Multi-tenancy isolation is defense-in-depth** (app scope + Postgres RLS + index namespacing) **plus AI-layer isolation** (ADR-0006).
- **Human-in-command** for consequential/irreversible agent actions; least privilege for services, agents, and plugins.
- **Defensive-only**: no offensive/attack-automation capabilities.

---

# 8. Documentation Conventions

Enforced by `docs/00-Governance/DocumentationStandards.md` and `NamingConventions.md`:

- Every doc starts with YAML front-matter: `title, document_id, status, version, last_updated, owner, audience, phase` (+ optional `related`). `document_id` uses fixed area prefixes (GOV, PRJ, VIS, ARC, MVP, BE, FE, DB, AI, MLO, SEC, DEP, API, AGT, PLG, TST, OPS). ADR files use the ADR template instead.
- One topic per file; use **relative links** for all cross-references — never restate content, link to the authoritative doc.
- Tag maturity honestly: **CURRENT / MVP / FUTURE / RESEARCH / EXPERIMENTAL**, and open items as **REQUIRES RESEARCH / REQUIRES DECISION**. Almost everything is MVP/FUTURE today — do not tag anything CURRENT unless the code/infra actually exists.
- Any new or renamed doc must be added to `docs/SUMMARY.md`; new terms go in `docs/01-Project/Glossary.md` in the same change.
- Diagrams are Mermaid fenced blocks (diffable, no binary assets).

---

# 9. Verifying Documentation Changes

There is no CI yet, so run these checks manually after editing docs (from the repo root, using the Bash tool / Git Bash).

Check all relative Markdown links resolve:

```bash
while IFS= read -r f; do d=$(dirname "$f"); \
  grep -oE '\]\(([^)]+\.md)(#[^)]*)?\)' "$f" | sed -E 's/\]\(//; s/\)$//; s/#.*$//' | \
  while read -r l; do case "$l" in http*) continue;; esac; [ -f "$d/$l" ] || echo "BROKEN: $f -> $l"; done; \
done < <(find . -name '*.md')
```

Check no old placeholder names crept back in (expect matches only inside `docs/adr/ADR-0001-*`, which documents the rename):

```bash
grep -rn 'Aegis\|SecLLM' .
```

When renaming a doc, update every inbound link and `docs/SUMMARY.md`, then re-run the link check.

---

# 10. Tooling & Engineering Capabilities

This section defines how Claude Code must select and use tools, CLIs, development
environments, plugins/skills/hooks/MCP servers, and AI/ML, security, and infrastructure
tooling across the Dula lifecycle. The objective is not to use every available tool — it is
to use the **right tool for the current phase and task** while preserving security,
reproducibility, maintainability, and governance.

## 10.1 General Tooling Principles

Determine which tools are actually required before doing substantial work. Selection must
consider: current phase, milestone, and task; the accepted architecture (§6); security,
testing, and deployment requirements; AI/ML needs; repository governance; reproducibility;
and maintenance cost.

Do not introduce a tool just because it is available. Every added tool can introduce a
dependency, attack surface, licensing obligation, maintenance burden, operational
complexity, reproducibility concern, or supply-chain risk. **Prefer the simplest tool that
correctly solves the problem**, and prefer tools already in the accepted stack over new ones.

Anything that ships **in the product** (runtime library, datastore, model, service) is
governed by the ADR process (§6) and the license/scan gates in
`docs/01-Project/Dependencies.md` and `docs/10-Security/SupplyChainSecurity.md`. Dev-only
tooling is lighter-weight but still kept minimal and reproducible (pinned, lockfiled).

## 10.2 Tool Categories → Accepted Stack

The engineering capability areas, each bound to the accepted architecture (§6). Do not
substitute a different technology for these without a new/superseding ADR.

```text
Repository / Git → gh CLI, Conventional Commits (docs/00-Governance/RepositoryGovernance.md)
Code Development → Python 3.12 + uv + ruff + mypy; TypeScript + pnpm + eslint; Go (data-plane)
Build / Packaging → uv, pnpm, Docker (signed images, SBOM)
Testing → pytest, vitest, Playwright (docs/15-Testing/)
Security → SAST, dependency/secret/container/IaC scans, red-team (docs/10-Security/)
Database → PostgreSQL 16 + Alembic
Vector / Search → Qdrant (vectors) + OpenSearch (BM25 / log-analytics)
Events / Streaming → Redpanda (Kafka API)
Containers → Docker
Kubernetes → Helm + Argo CD
Infrastructure as Code → Terraform
AI / LLM serving → vLLM (GPU) + llama.cpp (CPU/air-gap) + Ollama (dev), behind the LLM Gateway
RAG → Qdrant + OpenSearch + open embedding models
Agents → LangGraph + first-party permission/approval/audit layer
MLOps → MLflow + DVC + Argo Workflows
Observability → OpenTelemetry + Prometheus + Grafana + Loki + Tempo
Secrets → HashiCorp Vault + SOPS
Documentation → Markdown + Mermaid + the link-check in §9
Research → WebSearch / WebFetch (findings verified per §10.4)
```

## 10.3 Phase-Appropriate Tooling

Most of the stack above is **not stood up yet** (see §4). Tooling is introduced when its
phase arrives — do not scaffold or run tooling for infrastructure that does not exist.

| From | Tooling that becomes relevant |
|------|-------------------------------|
| Phase 01 (Foundation) | git/gh, CI (GitHub Actions), Python+TS toolchains, Docker Compose, Postgres/Alembic, Keycloak/OPA, base Helm charts, the scan gates |
| Phase 02 (Core Platform) | Redpanda, workers, OPA policy testing |
| Phase 03 (Knowledge & RAG) | LLM Gateway, vLLM/llama.cpp/Ollama, Qdrant, OpenSearch, embedding models, eval harness |
| Phase 04+ (Dula AI / MLOps) | MLflow, DVC, Argo Workflows, training/eval pipelines |
| Phase 06–07 (Agents / Plugins) | LangGraph, plugin host + sandbox |
| Phase 09–10 (Production / MLOps at scale) | Argo CD, Terraform, full OTel stack, GPU serving pools |

Details and per-phase Definition of Done: `docs/04-MVP-Roadmap/`.

## 10.4 Claude Code Capabilities (Skills, Subagents, Hooks, MCP)

- **Skills** — invoke a relevant skill when it fits the task (e.g. `code-review` /
  `security-review` before merging security-critical changes; `init`/repo skills for
  scaffolding). Load the skill before doing the work it governs.
- **Subagents** — use only when the user asks or a named agent clearly fits; do not
  over-spawn. Prefer handling work inline with your own tools; relay what matters from any
  agent's result.
- **Hooks** — automated, harness-executed behaviors configured in `settings.json` (e.g.
  running the §9 link-check or lint on save/stop). Standing "always do X" automation belongs
  in hooks, not in memory or ad-hoc habit.
- **MCP servers** — add only with a clear need and security review; they must respect the
  air-gapped constraint (no mandatory external calls) and their output is treated as
  **untrusted** like any external content.
- **Research grounding** — treat WebSearch/WebFetch results and all AI output as drafts to
  be verified against primary sources per `docs/00-Governance/AIContributionGuidelines.md`;
  never assert unverified facts (mark **REQUIRES RESEARCH** instead).

## 10.5 Tooling Guardrails

- **Do not invent commands** for infrastructure that does not exist yet (§4).
- **New product dependencies/tools** pass the license gate + SBOM + vulnerability/secret
  scans before adoption; structural choices require an ADR.
- **Air-gapped first** — any tool used in the product must work offline or be mirrorable
  into a private registry; no phone-home.
- **Secrets** are never embedded in commands, logs, or tool arguments; source them from
  Vault. Treat all tool/model/plugin output as untrusted.
- **Reproducibility** — pin and lock dev tools; record versions; prefer declarative config
  over imperative one-offs.

---

# 11. Phase & Milestone Documentation Closure (MANDATORY)

Documentation is **part of the Definition of Done**, not optional follow-up work. A
milestone or phase is **not complete** until its required technical *and* user/operator
documentation exists, is accurate, and is verified. This section makes it impossible to
reasonably declare a milestone complete while its required documentation is missing.

This section governs the *lifecycle*; it does not restate the authoring rules in
`docs/00-Governance/DocumentationStandards.md` (front matter, maturity tags, diagrams,
review) or `docs/00-Governance/NamingConventions.md` — those still apply.

## 11.1 The Closure Lifecycle

Every milestone and every phase follows this order; documentation is a gate, not a coda:

```text
Implementation
    ↓
Testing
    ↓
Security Validation
    ↓
Documentation            ← technical AND user/operator (this section)
    ↓
Milestone Review         ← Documentation Impact Assessment (§11.5) + checklist (§11.6)
    ↓
Project State Update     ← PROJECT_STATE.md (+ PROJECT_CONTEXT.md if durable knowledge changed)
    ↓
Milestone Closure        ← Milestone Closure Report (§11.7); status COMPLETE or DOCUMENTATION-INCOMPLETE
```

## 11.2 Two Documentation Audiences

Every milestone must be assessed against **both** audiences. They are distinct and must
not be conflated:

- **Technical / Engineering Documentation** — for developers, architects, security
  engineers, ML engineers, DevOps/SRE, and maintainers. Explains *how it works* and *how
  it is built* (architecture, implementation, contracts, operations). Lives in the existing
  numbered areas `docs/00-Governance` … `docs/16-Operations` (and `docs/adr/`).
- **User / Operator Documentation** — for end users, administrators, operators, and
  platform users. Explains *how to use / run / operate* the capability, without exposing
  unnecessary internal implementation detail. Lives in **`docs/17-User-Documentation/`**
  (see its `README.md`).

## 11.3 Technical Documentation Categories (assess every milestone)

For each completed milestone, **explicitly determine** which of these apply and create or
update them; record the categories that are **intentionally not applicable** (§11.5 Q6). Do
not create documents irrelevant to the milestone.

Architecture · Component · API · Database · Configuration · Security · Deployment ·
Infrastructure · AI/LLM · Model · RAG · Agent · Plugin/Integration · Testing ·
Troubleshooting · Operational/Runbook · Performance · Monitoring/Observability ·
Disaster-Recovery/Backup (where applicable) · Migration/Upgrade (where applicable).

These map to the existing areas (e.g. API→`12-API`, Database→`07-Database`,
Security→`10-Security`, AI/RAG→`08-AI`, Agents→`13-Agents`, Plugins→`14-Plugins`,
Runbooks/Monitoring/DR→`16-Operations`, Deployment→`11-Deployment`).

## 11.4 User / Operator Documentation Categories (where applicable)

Product overview · Installation guide · Getting-started guide · Configuration guide · User
guide · Administrator guide · Operator guide · Feature-usage guide · API-usage guide (where
applicable) · Troubleshooting guide · FAQ (where useful) · Security considerations ·
Deployment guide · Upgrade/migration guide · Backup/restore guide (where applicable).

These live under `docs/17-User-Documentation/`. Create a user guide only once the
corresponding capability is actually usable by that audience.

## 11.5 When to Create Documentation

- **Do not** wait until the end of the project (or even the end of the phase) to document.
- Create documentation **incrementally**, as functionality becomes stable.
- **Update** documentation whenever behavior changes.
- Complete **milestone-specific** documentation **before** milestone closure.
- **Do not document functionality that does not exist.** Mark planned work **FUTURE**,
  experimental work **EXPERIMENTAL**, and unresolved items **REQUIRES RESEARCH** /
  **REQUIRES DECISION**; never present FUTURE work as CURRENT. Maturity tags follow
  `docs/00-Governance/DocumentationStandards.md`. Documentation must always reflect the
  **actual implementation state**.
- Clearly mark **incomplete** documentation where it exists.

## 11.6 Documentation Impact Assessment (required at every milestone review)

At the end of every milestone, answer these explicitly (in the Milestone Closure Report):

1. What functionality was implemented?
2. What technical documentation was created?
3. What existing technical documentation was updated?
4. What user documentation was created?
5. What existing user documentation was updated?
6. What documentation was intentionally **not** created because it is not applicable?
7. Are all examples and commands verified against the current implementation?
8. Are all links valid?
9. Are screenshots/diagrams required (and present)?
10. Are any documentation items still incomplete?
11. Are there any known documentation gaps?

## 11.7 Milestone Documentation Checklist

Copy this into each Milestone Closure Report and resolve every item (`[x]` done, `[~]`
partial, `[N/A]` not applicable with reason). Unresolved required items block closure.

### Technical Documentation
- [ ] Architecture updated
- [ ] API documentation updated
- [ ] Database documentation updated
- [ ] Configuration documented
- [ ] Security documentation updated
- [ ] Deployment documentation updated
- [ ] Testing documentation updated
- [ ] Troubleshooting documentation updated
- [ ] Operational documentation updated
- [ ] AI/ML documentation updated where applicable
- [ ] RAG documentation updated where applicable
- [ ] Agent documentation updated where applicable
- [ ] Plugin/integration documentation updated where applicable

### User Documentation
- [ ] Getting Started updated
- [ ] Installation updated
- [ ] Configuration guide updated
- [ ] User guide updated
- [ ] Administrator guide updated where applicable
- [ ] Operator guide updated where applicable
- [ ] Feature documentation updated
- [ ] Troubleshooting updated
- [ ] FAQ updated where useful

### Documentation Quality
- [ ] Front matter follows DocumentationStandards.md
- [ ] Naming follows NamingConventions.md
- [ ] Relative links validated (`tools/check-doc-links.sh`)
- [ ] Mermaid diagrams validated where applicable
- [ ] Commands verified
- [ ] Configuration examples verified
- [ ] API examples verified
- [ ] No undocumented implemented functionality
- [ ] No implemented functionality incorrectly marked FUTURE
- [ ] No future functionality presented as CURRENT
- [ ] Documentation added to docs/SUMMARY.md
- [ ] Relevant glossary terms added
- [ ] PROJECT_CONTEXT.md updated where necessary
- [ ] PROJECT_STATE.md updated

## 11.8 Milestone Closure Report (required before COMPLETE)

Before a milestone may be declared **COMPLETE**, create/update its closure report at
`docs/04-MVP-Roadmap/closure/M0NN-<slug>-Closure.md` (see that folder's `README.md`). It
must contain: Milestone identifier · Milestone name · Objective · Scope · Implemented
functionality · Technical changes · Architecture changes · Database changes · API changes ·
Security changes · AI/ML changes (where applicable) · Testing performed · Security
validation performed · Deployment validation · Documentation completed (with the §11.6
assessment and §11.7 checklist) · Known limitations · Known issues · Deferred work ·
Lessons learned · Next milestone · Documentation gaps · **Final status**.

**Status rule:** if implementation, tests, and security are done but required documentation
is **not**, the milestone status is **`DOCUMENTATION-INCOMPLETE`**, never `COMPLETE`. A
milestone is `COMPLETE` only when its required technical *and* user documentation exist and
are verified.

## 11.9 Phase Completion Process

When an entire phase completes, in addition to the per-milestone closures, Claude Code must:

1. Review all milestones in the phase. 2. Verify each milestone's closure report exists.
3. Verify technical documentation is internally consistent. 4. Verify user documentation
matches the implemented product. 5. Remove or update obsolete documentation. 6. Verify
cross-document links. 7. Verify terminology (Glossary). 8. Verify architecture consistency.
9. Verify security guidance. 10. Update `PROJECT_CONTEXT.md`. 11. Update `PROJECT_STATE.md`.
12. Create a **Phase Completion Review** at
`docs/04-MVP-Roadmap/closure/PhaseNN-<slug>-Completion-Review.md`. 13. Identify remaining
documentation gaps. 14. Define documentation requirements for the next phase.

The **Phase Completion Review** must include: Phase objective · Milestones completed ·
Features delivered · Architecture delivered · Security posture · Testing status ·
Documentation status · User-documentation status · Known limitations · Technical debt ·
Deferred items · Lessons learned · Outstanding risks · Next-phase prerequisites.

## 11.10 Documentation Ownership & No-Duplication

- Every document declares its **audience** in front matter, drawn from: Developer,
  Architect, Security Engineer, ML Engineer, DevOps/SRE, Administrator, Operator, End User,
  Project Maintainer.
- **Single source of truth.** Do not create duplicate documents holding the same
  authoritative information. If the information exists in an authoritative document, update
  it and **link** to it rather than copying it.
- **Technical ↔ user cross-references.** Where a capability has both a technical and a user
  document, link each to the other. The technical document explains implementation and
  architecture (in its numbered area, e.g. `docs/12-API/Authentication.md`); the user
  document explains how to use the capability (in `docs/17-User-Documentation/`, e.g.
  `docs/17-User-Documentation/AuthenticationUserGuide.md`). Do not expose unnecessary
  internal implementation detail to ordinary users.

## 11.11 Where Lifecycle Documentation Lives

- Technical docs → existing numbered areas `docs/00-Governance` … `docs/16-Operations`, `docs/adr/`.
- User/operator docs → `docs/17-User-Documentation/`.
- Milestone Closure Reports → `docs/04-MVP-Roadmap/closure/M0NN-<slug>-Closure.md`.
- Phase Completion Reviews → `docs/04-MVP-Roadmap/closure/PhaseNN-<slug>-Completion-Review.md`.

New documents must follow `DocumentationStandards.md` + `NamingConventions.md`, be added to
`docs/SUMMARY.md`, add glossary terms where relevant, use relative links, and must not
duplicate existing authoritative documentation.
