import { expect, test } from "@playwright/test";

// Core-flow smoke test. Requires the web app running locally (`pnpm --filter web dev`).
test("unauthenticated visitor is prompted to sign in", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("button", { name: /sign in with keycloak/i })).toBeVisible();
});

test("protected list pages require authentication", async ({ page }) => {
  await page.goto("/alerts");
  await expect(page.getByRole("heading", { name: /sign in required/i })).toBeVisible();
});
