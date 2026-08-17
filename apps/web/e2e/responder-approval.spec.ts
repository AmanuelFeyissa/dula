import { expect, test } from "@playwright/test";

import { loginAs } from "./helpers";

// raj: responder, Acme tenant. Runs the investigation agent and approves its consequential
// step; the trace must attribute the decision to "raj" by name, not by opaque subject (PR B).
test("responder starts an investigation and approves the consequential step (raj)", async ({
  page,
}) => {
  await loginAs(page, "raj", "raj");

  await page.goto("/agents");
  await expect(page.getByRole("heading", { name: "Investigation agent" })).toBeVisible();

  await page.getByRole("button", { name: "Start investigation" }).click();
  await expect(page.getByText("Your approval is required")).toBeVisible({ timeout: 15_000 });

  await page.getByRole("button", { name: "Approve and continue" }).click();

  await expect(page.getByText(/^Approved by raj$/)).toBeVisible({ timeout: 15_000 });
  await expect(page.getByText(/^completed$/i)).toBeVisible();
});
