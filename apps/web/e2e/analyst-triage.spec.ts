import { expect, test } from "@playwright/test";

import { loginAs } from "./helpers";

// maya: analyst, Acme tenant. Analysts can triage alerts (create + update) and open incidents,
// but cannot update an incident once opened (docs/12-API/Authorization.md role table) — the
// list/detail pages hide that control accordingly (lib/permissions.ts, PR D).
test.describe("analyst triage (maya)", () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, "maya", "maya");
  });

  test("can filter, open, and triage an alert", async ({ page }) => {
    await page.goto("/alerts");
    await expect(page.getByRole("heading", { name: "Alerts", exact: true })).toBeVisible();

    await page.getByLabel("Severity").selectOption("critical");
    await page.getByRole("button", { name: "Filter" }).click();
    await expect(page).toHaveURL(/severity=critical/);

    const firstRow = page.locator("table.table tbody tr").first();
    await expect(firstRow).toBeVisible();
    await firstRow.locator("a").first().click();
    await expect(page).toHaveURL(/\/alerts\/[0-9a-f-]+/);

    // Analyst can update alerts (alerts.update) — the triage form must be visible.
    const triageForm = page.locator("form").filter({ has: page.locator("#status") });
    await expect(triageForm).toBeVisible();
    await page.getByLabel("Status").selectOption("triaged");
    await triageForm.evaluate((form: HTMLFormElement) => form.requestSubmit());

    // Scoped to the definition list's Status row specifically — a plain text search also
    // matches the (still-present, just closed) <option> in the triage <select>. The server
    // action's redirect + re-render round trip can run past the default 5s under load.
    await expect(page.locator("dt:has-text('Status') + dd")).toHaveText("triaged", {
      timeout: 10_000,
    });
  });

  test("cannot update an incident, but can create one", async ({ page }) => {
    await page.goto("/incidents");
    // Create link is offered (analyst has incidents.create).
    await expect(page.getByRole("link", { name: /new incident/i })).toBeVisible();

    const firstRow = page.locator("table.table tbody tr").first();
    const rowLink = firstRow.locator("a").first();
    await rowLink.waitFor({ state: "visible" });
    await rowLink.click();
    await page.waitForURL(/\/incidents\/[0-9a-f-]+/, { timeout: 10_000 });

    // No triage form: analyst lacks incidents.update, so the control must be hidden — not
    // merely disabled, and not left to the backend to reject after the fact.
    await expect(page.getByRole("heading", { name: "Triage" })).not.toBeVisible();
  });
});
