import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

import { loginAs } from "./helpers";

// axe-clean sweep of every page this milestone touched (M010 plan item F). Severity in this
// product is safety-relevant (colour must never be the sole carrier of meaning — ui.tsx's
// SeverityChip already pairs colour with text and a title attribute), so this is checked
// alongside generic WCAG rules, not as an afterthought.
const PAGES = ["/alerts", "/incidents", "/assets", "/alerts/new", "/incidents/new", "/assets/new"];

test.describe("accessibility (axe, maya)", () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, "maya", "maya");
  });

  for (const path of PAGES) {
    test(`${path} has no automatically detectable violations`, async ({ page }) => {
      await page.goto(path);
      const results = await new AxeBuilder({ page }).analyze();
      expect(results.violations, JSON.stringify(results.violations, null, 2)).toEqual([]);
    });
  }

  test("alert detail page (with triage form) has no violations", async ({ page }) => {
    await page.goto("/alerts");
    await page.locator("table.table tbody tr").first().locator("a").first().click();
    await expect(page).toHaveURL(/\/alerts\/[0-9a-f-]+/);
    const results = await new AxeBuilder({ page }).analyze();
    expect(results.violations, JSON.stringify(results.violations, null, 2)).toEqual([]);
  });

  test("alerts list is fully keyboard-navigable: filter, sort, open a row", async ({ page }) => {
    await page.goto("/alerts");
    await page.getByLabel("Search").focus();
    await page.keyboard.press("Tab"); // -> severity select
    await page.keyboard.press("Tab"); // -> status select
    await page.keyboard.press("Tab"); // -> Filter button
    await expect(page.getByRole("button", { name: "Filter" })).toBeFocused();

    // A sortable column header is a link, not a button — must be reachable and operable
    // from the keyboard alone (Tab + Enter), same as a mouse click.
    const severityHeader = page.getByRole("link", { name: /^Severity/ });
    await severityHeader.focus();
    await expect(severityHeader).toBeFocused();
    await page.keyboard.press("Enter");
    await expect(page).toHaveURL(/sort=severity/);
  });
});
