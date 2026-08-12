import { defineConfig, devices } from "@playwright/test";

// E2E config for core UI flows. Runs against a locally-running web app + dev stack
// (see docs/17-User-Documentation and docs/15-Testing/IntegrationTesting.md). Not part of
// the unit CI lane because it requires the full stack (Keycloak, Platform API).
export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  use: {
    baseURL: process.env.WEB_BASE_URL ?? "http://localhost:3000",
    trace: "on-first-retry",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
