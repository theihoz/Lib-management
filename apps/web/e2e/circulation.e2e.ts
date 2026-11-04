import { expect, test } from "@playwright/test";
import { checkout, login } from "./helpers";

test("checkout then return in good condition", async ({ page }) => {
  await login(page, "librarian.dev");
  await checkout(page, "DG0002", "DEMO-0001");
  await page.goto("/staff/returns");
  await page.getByLabel("Mã vạch bản sách").fill("DEMO-0001");
  await page.getByRole("button", { name: "Tìm khoản mượn" }).click();
  await page.getByRole("button", { name: "Ghi nhận trả sách" }).click();
  await expect(page.getByText("Biên nhận trả sách")).toBeVisible();
});

test("damaged return suggests the BM09 fee and the manager decides it", async ({ browser }) => {
  const desk = await (await browser.newContext()).newPage();
  await login(desk, "librarian.dev");
  await checkout(desk, "DG0003", "DEMO-0002");
  await desk.goto("/staff/returns");
  await desk.getByLabel("Mã vạch bản sách").fill("DEMO-0002");
  await desk.getByRole("button", { name: "Tìm khoản mượn" }).click();
  await desk.getByRole("radio", { name: "Hỏng" }).check();
  await expect(desk.getByLabel("Số tiền đề xuất (VND)")).toHaveValue("20000");
  await desk.getByRole("button", { name: "Ghi nhận trả sách" }).click();
  await expect(desk.getByText("Đã gửi Quản lý")).toBeVisible();

  const manager = await (await browser.newContext()).newPage();
  await login(manager, "manager.dev");
  await manager.goto("/manager/charge-assessments");
  const row = manager
    .getByRole("row")
    .filter({ hasText: "Hỏng" })
    .filter({ hasText: "Chờ quyết định" });
  await row.first().getByRole("button").click();
  await manager.getByLabel(/Số tiền/).fill("20000");
  await manager.getByLabel(/Lý do/).fill("Theo khung phí");
  await manager.getByRole("button", { name: "Xác nhận quyết định" }).click();
  await expect(manager.getByText("Đã tính phí")).toBeVisible();
});
