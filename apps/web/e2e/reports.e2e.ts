import { expect, test } from "@playwright/test";
import { login, today } from "./helpers";

test.beforeEach(async ({ page }) => {
  await login(page, "manager.dev");
});

test("BM08 report is built by the worker", async ({ page }) => {
  await page.goto("/manager/reports");
  await page.getByLabel("Loại báo cáo").selectOption("LOAN_TREND");
  await page.getByLabel("Từ ngày").fill(`${today().slice(0, 8)}01`);
  await page.getByLabel(/Đến ngày/).fill(today());
  await page.getByRole("button", { name: "Tạo báo cáo" }).click();
  await expect(page.getByText("Hoàn tất").first()).toBeVisible({ timeout: 30_000 });
  await expect(page.getByText("Biểu đồ lượt mượn theo thời gian")).toBeVisible();
});

test("QĐ13: the period may not end after today", async ({ page }) => {
  await page.goto("/manager/reports");
  const tomorrow = new Date(Date.parse(today()) + 86_400_000).toISOString().slice(0, 10);
  await page.getByLabel("Từ ngày").fill(today());
  await page.getByLabel(/Đến ngày/).fill(tomorrow);
  await expect(page.getByText("Ngày kết thúc không được sau hôm nay.")).toBeVisible();
});

test("QĐ26: an empty export creates no file", async ({ page }) => {
  await page.goto("/manager/exports");
  await page.getByLabel("Loại báo cáo").selectOption("FINE_CSV");
  await page.getByLabel("Từ ngày").fill("2001-01-01");
  await page.getByLabel(/Đến ngày/).fill("2001-01-02");
  await page.getByRole("button", { name: "Yêu cầu xuất CSV" }).click();
  await expect(page.getByText(/Không có dữ liệu phù hợp để xuất/)).toBeVisible({ timeout: 30_000 });
});

test("loans CSV downloads", async ({ page }) => {
  await page.goto("/manager/exports");
  await page.getByLabel("Loại báo cáo").selectOption("LOAN_CSV");
  await page.getByLabel("Từ ngày").fill(`${today().slice(0, 8)}01`);
  await page.getByLabel(/Đến ngày/).fill(today());
  await page.getByRole("button", { name: "Yêu cầu xuất CSV" }).click();
  const button = page.getByRole("button", { name: "Tải CSV" });
  await expect(button).toBeVisible({ timeout: 30_000 });
  const [download] = await Promise.all([page.waitForEvent("download"), button.click()]);
  expect(download.suggestedFilename()).toMatch(/\.csv$/);
});

test("policy draft validates QĐ17 before saving", async ({ page }) => {
  await page.goto("/manager/policies/new");
  const threshold = page.getByLabel("Ngưỡng chặn nợ phạt", { exact: true });
  await threshold.fill("0");
  await expect(page.getByText("Tối thiểu 1.")).toBeVisible();
  await threshold.fill("60000");
  const future = new Date(Date.now() + 7 * 3600e3 + 30 * 86_400_000).toISOString().slice(0, 16);
  await page.getByLabel("Hiệu lực từ (giờ thư viện)").fill(future);
  await page.getByRole("button", { name: "Lưu bản nháp" }).click();
  await expect(page).toHaveURL(/\/manager\/policies$/);
});
