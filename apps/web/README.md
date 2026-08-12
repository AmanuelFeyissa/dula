# web — Dula UI (Next.js)

Authenticated app shell (Phase 01): Keycloak OIDC login (Auth.js) + a page that calls the
Platform API's `GET /api/v1/me` server-side with the user's access token.

## Run locally
```bash
# 1) bring up the dev stack (Keycloak, Postgres, ...) from the repo root:
make up
# 2) run the platform API (repo root):
uv run uvicorn dula_platform_api.main:app --reload   # http://localhost:8000
# 3) web:
cp apps/web/.env.local.example apps/web/.env.local    # set AUTH_SECRET
pnpm --filter web install
pnpm --filter web dev                                 # http://localhost:3000
```
Log in with the seeded realm user **maya / maya**, then the home page shows the verified
claims returned by the API — proving the end-to-end OIDC path (ADR-0009).

See [../../docs/06-Frontend/FrontendArchitecture.md](../../docs/06-Frontend/FrontendArchitecture.md).
