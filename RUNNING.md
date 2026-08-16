# Running Dula locally

A practical, copy-paste guide to **start, use, and stop** the Dula platform on your machine —
with every URL and credential you need. This runs the **offline/dev profile** (no GPU, no heavy
data plane required); it is the fastest way to *see the system*.

> All credentials below are **local-development defaults only** (from `.env.example`). They are not
> secrets and must never be used in production — production secrets come from Vault (ADR-0015).

---

## 1. What you get (live URLs)

Once started (see §3), open these in your browser:

| Service | URL | What it is |
|---------|-----|------------|
| **Web app** | http://localhost:3000 | The Dula UI — sign in here |
| Platform API docs | http://localhost:8000/docs | Assets / incidents / alerts REST API (Swagger) |
| AI Gateway docs | http://localhost:8100/docs | Ask, Triage, Intel, Agents, Plugins, Automation (Swagger) |
| Keycloak admin | http://localhost:8080 | Identity provider admin console |
| OPA | http://localhost:8181 | Authorization policy engine |

Health checks: http://localhost:8000/healthz · http://localhost:8100/healthz

---

## 2. Credentials (local dev only)

### Web app personas

All six are seeded in the `dula` realm. Password = username in every case (dev only). The first
five share tenant **Acme**; `tariq` is in a **second tenant**, which is how you can see tenant
isolation with your own eyes.

| Sign in as | Password | Role | What it demonstrates |
|-----------|----------|------|----------------------|
| `maya` | `maya` | analyst | The default SOC analyst view; can create tickets |
| `admin` | `admin` | admin | Unrestricted — every action allowed |
| `raj` | `raj` | responder | Can approve containment (`isolate_host`) |
| `hana` | `hana` | hunter | Threat hunting; no asset management |
| `sam` | `sam` | engineer | Detection engineering; can manage assets |
| `tariq` | `tariq` | analyst (**other tenant**) | Sees only its own data — proves isolation |

### Infrastructure

| Where | Username | Password | Notes |
|-------|----------|----------|-------|
| Keycloak admin console | `admin` | `admin` | Realm to manage: **`dula`** (this is the *master*-realm admin) |
| PostgreSQL | `dula` | `dula_dev_password` | db `dula`, `localhost:5432` |
| OpenSearch (full stack only) | `admin` | `Dula_dev_Admin123!` | only if you start `opensearch` |
| MinIO (full stack only) | `dula` | `dula_dev_password` | console http://localhost:9001 |

**To log in:** open http://localhost:3000 → you land directly on the Dula sign-in page → enter one
of the personas above → you are back in the app, authenticated. There is no provider-chooser step:
Keycloak is the only identity provider, so the app starts the OIDC flow immediately and Keycloak
serves the page using the Dula theme in `deploy/docker/keycloak/themes/dula/`.

**Switching personas** is just Sign out → sign in as someone else. Signing out performs an
RP-initiated logout, which ends the Keycloak SSO session as well as Dula's own, so the next sign-in
really does prompt. No container restarts are needed.

Add more users by editing `deploy/docker/keycloak/realm/dula-realm.json`, then **recreating** the
Keycloak container — a plain restart won't re-import, because Keycloak skips import when the realm
already exists:

```bash
docker compose -f deploy/docker/docker-compose.dev.yml --env-file .env rm -sf keycloak
docker compose -f deploy/docker/docker-compose.dev.yml --env-file .env up -d keycloak
```

The same applies after editing the login theme's `theme.properties` or the realm's `loginTheme`.
Theme **CSS** edits need no restart (`start-dev` disables theme caching) — but if you change the
palette, regenerate the theme's copy of the design tokens first, or CI will fail the drift check:

```bash
node tools/sync-design-tokens.mjs          # regenerate
node tools/sync-design-tokens.mjs --check  # what CI runs
```

---

## 3. Start from scratch

### Prerequisites
- **Docker Desktop** (running), **Node 20+** with `pnpm` (via `corepack enable`), and
  [`uv`](https://docs.astral.sh/uv/) (manages Python 3.12). Install deps once:
  `uv sync` and `pnpm install`.

### 3a. Backing services (Postgres + Keycloak + OPA)
This light subset is enough for the full app experience in the offline profile:

```bash
docker compose -f deploy/docker/docker-compose.dev.yml --env-file .env up -d postgres opa keycloak
```

(For the **full** data plane too — Qdrant, OpenSearch, Redpanda, MinIO, Redis, Ollama — use
`make up` instead. It is much heavier on RAM/disk and is not needed just to see the system.)

### 3b. Database schema (migrations)
```bash
cd apps/platform-api && uv run alembic upgrade head && cd ../..
```

### 3b-2. Demo data (recommended)
Without this the app is empty and there is nothing to look at. Idempotent — safe to re-run:

```bash
docker exec -i dula-dev-postgres-1 psql -U dula -d dula < tools/seed-demo-data.sql
```

Seeds two tenants, 6 assets, 4 incidents, and 11 alerts across the severity range.

### 3c. The two API services (each in its own terminal)
```bash
# Platform API — http://localhost:8000
uv run --directory apps/platform-api uvicorn dula_platform_api.main:app --host 0.0.0.0 --port 8000

# AI Gateway — http://localhost:8100  (offline: extractive provider, in-memory stores)
DULA_EVENTS_ENABLED=false uv run --directory apps/ai-gateway uvicorn dula_ai_gateway.main:app --host 0.0.0.0 --port 8100
```

### 3d. The web app
```bash
cp apps/web/.env.local.example apps/web/.env.local     # first time only
pnpm --filter web dev                                  # http://localhost:3000
```

Then open **http://localhost:3000** and sign in with **`maya` / `maya`**.

> Tip: if `uv run` complains about the Anaconda environment, run `unset VIRTUAL_ENV` first (or
> `$env:VIRTUAL_ENV=$null` in PowerShell) so uv uses the project `.venv`.

---

## 4. What to try (feature tour)

Signed in as `maya`, the top navigation exposes everything built through Phase 08:

- **Alerts / Incidents / Assets** — browse the core security domain (create/update via the API).
- **Ask** — grounded, cited Q&A + alert **triage** (offline extractive model; no external calls).
- **Intel** — CTI extraction (IOCs + ATT&CK → STIX), CVSS vulnerability prioritization, and
  Sigma/YARA authoring.
- **Agents** — run the investigation assistant; it triages/enriches/corroborates and **pauses for
  your approval** before creating a ticket.
- **Integrations** — view connectors and run read-only lookups.
- **Automation** — run the `triage-enrich-ticket` **playbook**; approve the consequential step;
  **Generate report** for a grounded write-up.

Prefer the API directly? Explore and call every endpoint from the Swagger UIs at
http://localhost:8000/docs and http://localhost:8100/docs (click **Authorize** and paste a bearer
token — the web app carries one after login).

---

## 5. Stop / restart / clean up

```bash
# Stop the app processes: Ctrl+C in each terminal (API/web), or by port on Windows:
#   for p in 8000 8100 3000; do npx --yes kill-port $p; done

# Stop the backing services (keep data):
docker compose -f deploy/docker/docker-compose.dev.yml down
# ...or via the Makefile:  make down

# Stop AND wipe all local data volumes (fresh start next time):
docker compose -f deploy/docker/docker-compose.dev.yml down -v
```

Restarting later: repeat §3a → §3d. Data in Postgres/Keycloak persists across `down` (without
`-v`), so you can skip re-seeding.

---

## 6. Backup & restore drill (verified)

The Phase 09 DR scripts work against real Postgres:

```bash
export DATABASE_URL=postgres://dula:dula_dev_password@localhost:5432/dula
deploy/backup/pg-backup.sh ./backups                 # -> dula-<ts>.dump (+ .sha256)
deploy/backup/pg-restore.sh ./backups/dula-<ts>.dump # checksum-verified restore
```

See [deploy/backup/README.md](deploy/backup/README.md) and
[docs/11-Deployment/DisasterRecovery.md](docs/11-Deployment/DisasterRecovery.md).

---

## 7. Production / Kubernetes

Local dev uses Docker Compose; production uses the umbrella **Helm chart** with per-profile
overlays. See the operator guide
[docs/17-User-Documentation/InstallationGuide.md](docs/17-User-Documentation/InstallationGuide.md)
and [docs/11-Deployment/GAReadiness.md](docs/11-Deployment/GAReadiness.md).

---

## 8. Troubleshooting

| Symptom | Fix |
|---------|-----|
| Web sign-in doesn't redirect | Ensure Keycloak is up (http://localhost:8080/realms/dula returns 200) and `apps/web/.env.local` exists. |
| `uv run` uses the wrong Python | `unset VIRTUAL_ENV` (bash) / `$env:VIRTUAL_ENV=$null` (PowerShell) so uv uses `.venv`. |
| Port already in use | Stop the old process (`npx kill-port 8000 8100 3000`) or change the `--port`. |
| `/readyz` shows `database: error` | Postgres isn't up or migrations didn't run — see §3a/§3b. |
| Keycloak login fails for `maya` | Realm import may still be running; wait ~30s after `up`, then retry. |
| Docker won't start containers | Confirm Docker Desktop is running (`docker info`). |

---

## 9. Related guides

- Quickstart: [README.md](README.md)
- Local development detail: [docs/11-Deployment/LocalDevelopment.md](docs/11-Deployment/LocalDevelopment.md)
- Using features: [docs/17-User-Documentation/](docs/17-User-Documentation/README.md)
  (Ask, Cyber Intelligence, Investigation Agent, Integrations, Automation Playbooks guides)
- Install on Kubernetes: [docs/17-User-Documentation/InstallationGuide.md](docs/17-User-Documentation/InstallationGuide.md)
