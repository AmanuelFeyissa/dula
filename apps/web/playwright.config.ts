import { defineConfig, devices } from "@playwright/test";

// E2E config for core UI flows. Runs against a locally-running web app + dev stack
// (see docs/17-User-Documentation and docs/15-Testing/IntegrationTesting.md). Not part of
// the unit CI lane because it requires the full stack (Keycloak, Platform API).
export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  // Capped rather than the platform default (CPU core count): against `next dev` — the
  // documented local setup, RUNNING.md §3d — every route compiles on first request, and
  // firing many first-time route hits at once (this suite spans ~10 distinct routes) starves
  // the dev server into 15-30s timeouts unrelated to any real bug. Verified: the same specs
  // pass reliably at this worker count and fail broadly at the unbounded default. A built app
  // (`next build && next start`) wouldn't need this, but that isn't the local dev workflow.
  workers: 4,
  use: {
    baseURL: process.env.WEB_BASE_URL ?? "http://localhost:3000",
    trace: "on-first-retry",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
