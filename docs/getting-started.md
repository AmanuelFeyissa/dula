---
title: Getting Started
---

# Getting started

This guide gets you from a clone to a running Dula instance with grounded Q&A, on your own
machine. It uses the local stack (Docker Compose for the backing services, the API services run
from source) — the same topology as production, at small scale.

!!! note "Prerequisites"
    - **Docker** (Desktop or Engine) for the backing services.
    - **[uv](https://docs.astral.sh/uv/)** for the Python services, and **Node + pnpm** for the web UI.
    - Git. ~6 GB of disk for the service images.

## 1. Clone and start the backing services

```bash
git clone https://github.com/AmanuelFeyissa/dula.git
cd dula
cp .env.example .env          # local-only dev values; never real secrets
make up                       # Postgres, Redis, Qdrant, OpenSearch, Redpanda, OPA, Keycloak
make ps                       # all services should become healthy
```

The default stack excludes object storage (MinIO); enable it with
`docker compose -f deploy/docker/docker-compose.dev.yml --profile storage up -d` if you need it.

## 2. Apply database migrations

```bash
cd apps/platform-api
uv run alembic upgrade head   # creates tenants, alerts, incidents, assets, audit tables
cd ../..
```

## 3. Run the services

=== "Platform API"

    ```bash
    cd apps/platform-api
    uv run uvicorn dula_platform_api.main:app --port 8000
    ```

=== "AI Gateway"

    ```bash
    cd apps/ai-gateway
    uv run uvicorn dula_ai_gateway.main:app --port 8001
    ```

=== "Web UI"

    ```bash
    cd apps/web
    pnpm install && pnpm dev     # http://localhost:3000
    ```

Interactive API docs are then at **http://localhost:8000/docs** (Platform API) and
**http://localhost:8001/docs** (AI Gateway).

## 4. Sign in and get a token

The dev Keycloak realm ships with test users (password = username): `maya` (analyst), `raj`
(responder), `hana` (hunter), `sam` (engineer), `admin` (admin) in one tenant, and `tariq`
(analyst) in a second tenant for testing isolation.

```bash
curl -s -X POST http://localhost:8080/realms/dula/protocol/openid-connect/token \
  -d 'grant_type=password&client_id=dula-web&username=maya&password=maya&scope=openid' \
  | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])"
```

!!! tip "Direct token grant"
    If the token request is rejected, enable **Direct access grants** on the `dula-web` client in
    the Keycloak admin console (http://localhost:8080, `admin`/`admin`) → Clients → dula-web.

## 5. Ask Dula something

```bash
TOKEN=...   # the access token from step 4
curl -s -X POST http://localhost:8001/api/v1/ask \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"question":"What is Log4Shell and how do I mitigate it?"}'
```

You get a **grounded** answer with citations. From here:

- [Using Dula](17-User-Documentation/README.md) — the end‑user guides (Ask, triage, intel, agents, playbooks).
- [Deployment profiles](11-Deployment/README.md) — run Dula on Kubernetes, cloud, on‑prem, hybrid, or air‑gapped.
- [Authentication](12-API/Authentication.md) and [Authorization](12-API/Authorization.md) — wire up your own identity provider and roles.

!!! warning "Production deployment"
    The steps above are the **local/dev** path. Published container images and a production install
    are part of GA readiness ([GA readiness](11-Deployment/GAReadiness.md)); for a real cluster use
    the Helm chart under `deploy/helm/dula` with the profile overlay that matches your environment.
