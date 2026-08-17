import { expect, test } from "@playwright/test";

// Core-flow smoke test. Requires the web app + Keycloak running locally (RUNNING.md §3).
// The Dula-themed Keycloak realm and login theme (PR A) mean there is no app-side interstitial
// — an unauthenticated visitor lands directly on the Dula-branded Keycloak login page.
test("unauthenticated visitor is redirected straight to the Dula-themed login, no interstitial", async ({
  page,
}) => {
  await page.goto("/");
  await page.waitForURL(/\/realms\/dula\/protocol\/openid-connect\//);
  await expect(page.locator("#kc-form-login")).toBeVisible();
  // No Keycloak default branding string ever reaches the page title/body copy.
  await expect(page.locator("body")).not.toContainText("Keycloak");
});

test("protected list pages redirect to sign-in the same way", async ({ page }) => {
  await page.goto("/alerts");
  await page.waitForURL(/\/realms\/dula\/protocol\/openid-connect\//);
  await expect(page.locator("#kc-form-login")).toBeVisible();
});
