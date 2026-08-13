# Dula web (Next.js) image. Build from the REPO ROOT (pnpm workspace context):
#   docker build -f apps/web/Dockerfile -t dula/web .
# Multi-stage; standalone output; non-root runtime; no telemetry phone-home (air-gapped-safe).
FROM node:20-slim AS deps
ENV PNPM_HOME=/pnpm PATH="/pnpm:$PATH" NEXT_TELEMETRY_DISABLED=1
RUN corepack enable
WORKDIR /app
# Workspace manifests first for better layer caching.
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY apps/web/package.json apps/web/package.json
RUN pnpm install --frozen-lockfile --filter web...

FROM node:20-slim AS build
ENV PNPM_HOME=/pnpm PATH="/pnpm:$PATH" NEXT_TELEMETRY_DISABLED=1
RUN corepack enable
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY --from=deps /app/apps/web/node_modules ./apps/web/node_modules
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY apps/web ./apps/web
# AUTH_SECRET is only needed at runtime; a build-time placeholder keeps `next build` happy.
ENV AUTH_SECRET=build-time-placeholder-not-used-at-runtime
RUN pnpm --filter web build

FROM node:20-slim AS runtime
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1 PORT=3000 HOSTNAME=0.0.0.0
RUN useradd --uid 10001 --create-home dula
WORKDIR /app
# Standalone server + traced node_modules, then static assets and public files.
COPY --from=build /app/apps/web/.next/standalone ./
COPY --from=build /app/apps/web/.next/static ./apps/web/.next/static
COPY --from=build /app/apps/web/public ./apps/web/public
USER dula
EXPOSE 3000
CMD ["node", "apps/web/server.js"]
