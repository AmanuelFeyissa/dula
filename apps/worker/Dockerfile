# Dula event worker image. Build from the REPO ROOT (workspace context):
#   docker build -f apps/worker/Dockerfile -t dula/worker .
# Multi-stage with uv; non-root runtime (docs/10-Security/SecureDevelopment.md).
FROM python:3.12-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:0.12 /uv /uvx /bin/
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
WORKDIR /app

# Workspace metadata first (better layer caching).
COPY pyproject.toml uv.lock ./
COPY packages/common-py/pyproject.toml packages/common-py/
COPY apps/worker/pyproject.toml apps/worker/
# Source.
COPY packages/common-py packages/common-py
COPY apps/worker apps/worker
RUN uv sync --frozen --package dula-worker --no-dev

FROM python:3.12-slim AS runtime
RUN useradd --create-home --uid 10001 dula
WORKDIR /app
COPY --from=builder /app /app
ENV PATH="/app/.venv/bin:$PATH"
USER dula
CMD ["python", "-m", "dula_worker.main"]
