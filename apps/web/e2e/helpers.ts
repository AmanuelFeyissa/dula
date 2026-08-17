import type { Page } from "@playwright/test";

/**
 * Sign in through the real Dula-themed Keycloak flow (PR A) and land back on the app.
 *
 * Submits via `form.requestSubmit()` rather than clicking the "Sign in" button: this session's
 * persona testing repeatedly found that a synthetic Playwright `.click()` on Keycloak's login
 * button (and on the app's own server-action submit buttons) doesn't reliably trigger the
 * underlying form submission, causing intermittent flakes. Requesting the form's own submission
 * is the reliable equivalent of what a real click does at the browser level.
 */
export async function loginAs(page: Page, username: string, password: string): Promise<void> {
  await page.goto("/");
  await page.waitForURL(/\/realms\/dula\/protocol\/openid-connect\//);
  await page.locator("#username").fill(username);
  await page.locator("#password").fill(password);
  await page.locator("#kc-form-login").evaluate((form: HTMLFormElement) => form.requestSubmit());
  await page.waitForURL((url) => url.port !== "8080", { timeout: 15_000 });
}

/**
 * Submit a plain (no-JS-required) server-action `<form>` via `requestSubmit()` — the same
 * workaround as `loginAs`, for the app's own triage/create forms (PR D).
 */
export async function submitForm(page: Page, formSelector: string): Promise<void> {
  await page.locator(formSelector).evaluate((form: HTMLFormElement) => form.requestSubmit());
}
