# Dula AI Gateway image. Build from the REPO ROOT (workspace context):
#   docker build -f apps/ai-gateway/Dockerfile -t dula/ai-gateway .
# Multi-stage with uv; non-root runtime (docs/10-Security/SecureDevelopment.md).
FROM python:3.12-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:0.12 /uv /uvx /bin/
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
WORKDIR /app

# Workspace metadata first (better layer caching). The AI Gateway depends on the full
# workspace stack: common-py, dula-ai, dula-agents, dula-plugins, dula-automation.
COPY pyproject.toml uv.lock ./
COPY packages/common-py/pyproject.toml packages/common-py/
COPY packages/dula-ai/pyproject.toml packages/dula-ai/
COPY packages/dula-agents/pyproject.toml packages/dula-agents/
COPY packages/dula-plugins/pyproject.toml packages/dula-plugins/
COPY packages/dula-automation/pyproject.toml packages/dula-automation/
COPY apps/ai-gateway/pyproject.toml apps/ai-gateway/
# Source.
COPY packages/common-py packages/common-py
COPY packages/dula-ai packages/dula-ai
COPY packages/dula-agents packages/dula-agents
COPY packages/dula-plugins packages/dula-plugins
COPY packages/dula-automation packages/dula-automation
COPY apps/ai-gateway apps/ai-gateway
RUN uv sync --frozen --package dula-ai-gateway --no-dev

FROM python:3.12-slim AS runtime
RUN useradd --create-home --uid 10001 dula
WORKDIR /app
COPY --from=builder /app /app
ENV PATH="/app/.venv/bin:$PATH"
USER dula
EXPOSE 8100
CMD ["uvicorn", "dula_ai_gateway.main:app", "--host", "0.0.0.0", "--port", "8100"]
