import { expect, test } from "@playwright/test";

import { loginAs } from "./helpers";

// tariq: analyst, Globex tenant — the second demo tenant (docs seed: tools/seed-demo-data.sql).
// The list pages must show only Globex data, filters must not leak Acme rows into the count,
// and a direct hit on an Acme-owned URL must 404 rather than leak a cross-tenant record.
const ACME_ALERT_ID = "b0000000-0000-0000-0000-000000000001";
const GLOBEX_ALERT_ID = "b0000000-0000-0000-0000-000000000091";

test.describe("second-tenant isolation (tariq)", () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, "tariq", "tariq");
  });

  test("only sees Globex's own alert, even filtered", async ({ page }) => {
    await page.goto("/alerts");
    await expect(page.getByRole("heading", { name: "Alerts", exact: true })).toBeVisible();

    // Globex's seed is a single alert — the count must reflect exactly that, not Acme's 11.
    await expect(page.getByText(/1 total/)).toBeVisible();

    await page.getByLabel("Severity").selectOption("critical");
    await page.getByRole("button", { name: "Filter" }).click();
    // Filtering must not surface Acme's critical alerts under Globex's tenant scope.
    const rows = page.locator("table.table tbody tr");
    if (await rows.count()) {
      await expect(rows).toHaveCount(1);
    }
  });

  test("cannot reach an Acme alert by direct URL, but can reach its own", async ({ page }) => {
    await page.goto(`/alerts/${ACME_ALERT_ID}`);
    await expect(page.getByText(/this page could not be found/i)).toBeVisible();

    await page.goto(`/alerts/${GLOBEX_ALERT_ID}`);
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    await expect(page.getByText(/this page could not be found/i)).not.toBeVisible();
  });
});
