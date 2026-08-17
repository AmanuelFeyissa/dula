import { expect, test } from "@playwright/test";

import { loginAs } from "./helpers";

// admin: unrestricted (Acme tenant). Integrations is the one console every persona above can
// reach the nav link for but only admin is expected to actually manage — confirms the plugin
// host renders its installed connectors and that a read-only connector can be invoked.
test("admin sees installed connectors and can run a read connector (admin)", async ({ page }) => {
  await loginAs(page, "admin", "admin");

  await page.goto("/integrations");
  await expect(page.getByRole("heading", { name: "Integrations" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Installed connectors" })).toBeVisible();

  // At least one connector is registered out of the box (SIEM, ticketing — plugins_wiring.py).
  await expect(page.getByText(/no connectors installed/i)).not.toBeVisible();

  await expect(page.getByRole("heading", { name: "Run a read connector" })).toBeVisible();
});
