import { expect, test } from "@playwright/test";
import { login } from "./helpers";

test("librarian, manager and reader sign in through Keycloak", async ({ browser }) => {
  for (const user of ["librarian.dev", "manager.dev", "reader.dev"]) {
    const page = await (await browser.newContext()).newPage();
    await login(page, user);
    await page.close();
  }
});

test("a reader never sees staff screens", async ({ page }) => {
  await login(page, "reader.dev");
  const nav = page.getByRole("navigation").first();
  await expect(nav).not.toContainText("Mượn sách");
  await expect(nav).not.toContainText("Trả sách");
});

test("staff land on the dashboard (YC#19)", async ({ page }) => {
  await login(page, "librarian.dev");
  await page.goto("/staff");
  await expect(page).toHaveURL(/\/staff\/dashboard/);
  await expect(page.getByRole("heading", { name: "Sách được mượn nhiều nhất" })).toBeVisible();
});
