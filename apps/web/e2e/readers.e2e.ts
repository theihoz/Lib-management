import { expect, test } from "@playwright/test";
import { login, pickReader } from "./helpers";

test("lock and unlock a card (YC#6)", async ({ page }) => {
  await login(page, "librarian.dev");
  await page.goto("/staff/readers");
  await page.getByRole("button", { name: "DG0004" }).click();
  const cards = page.getByRole("table", { name: /Thẻ thư viện/ });
  await cards.getByRole("button").first().click();
  await page.getByLabel("Lý do").fill("Mất thẻ");
  await page.getByRole("button", { name: "Khóa thẻ" }).click();
  await expect(cards.getByRole("cell", { name: "Tạm khóa" })).toBeVisible();
  await expect(page.getByText("Thẻ đang tạm khóa")).toBeVisible();
  await cards.getByRole("button").first().click();
  await page.getByRole("button", { name: "Mở khóa" }).click();
  await expect(cards.getByRole("cell", { name: "Hoạt động" })).toBeVisible();
  for (const title of ["Đang mượn", "Phạt chưa thu", "Đặt trước đang chờ", "Lịch sử mượn trả"])
    await expect(page.getByRole("heading", { name: title })).toBeVisible();
});

test("manual fine is proposed by the librarian and confirmed by the manager (YC#11)", async ({
  browser,
}) => {
  const desk = await (await browser.newContext()).newPage();
  await login(desk, "librarian.dev");
  await desk.goto("/staff/finance");
  await pickReader(desk, "DG0005");
  await desk.getByLabel("Số tiền (VND)").fill("12000");
  await desk.getByLabel("Lý do").fill("Viết vào sách");
  await desk.getByRole("button", { name: "Gửi đề xuất" }).click();
  await expect(desk.getByText("Đã gửi đề xuất cho Quản lý.")).toBeVisible();

  const manager = await (await browser.newContext()).newPage();
  await login(manager, "manager.dev");
  await manager.goto("/manager/charge-assessments");
  const row = manager
    .getByRole("row")
    .filter({ hasText: "Thủ công" })
    .filter({ hasText: "Chờ quyết định" });
  await row.first().getByRole("button").click();
  await manager.getByLabel(/Số tiền/).fill("12000");
  await manager.getByLabel(/Lý do/).fill("Đúng quy định");
  await manager.getByRole("button", { name: "Xác nhận quyết định" }).click();
  await expect(manager.getByText("Đã tính phí")).toBeVisible();
});
