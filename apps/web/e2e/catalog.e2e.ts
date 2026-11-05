import { expect, test } from "@playwright/test";
import { login } from "./helpers";

test.beforeEach(async ({ page }) => {
  await login(page, "librarian.dev");
});

test("copy status Sẵn sàng → Bảo trì → Sẵn sàng (YC#2)", async ({ page }) => {
  await page.goto("/staff/catalog");
  await page.getByLabel("Tìm sách").fill("Mắt biếc");
  // Wait for the debounced search to narrow the list before opening the edition.
  await page.getByRole("row").filter({ hasText: "Mắt biếc" }).getByRole("button").first().click();
  const edition = page.url().match(/[0-9a-f-]{36}/)![0];
  await page.goto(`/staff/catalog/copies?edition=${edition}`);
  await page.getByRole("row").filter({ hasText: "Sẵn sàng" }).first().getByRole("button").click();
  await page.getByLabel("Trạng thái mới").selectOption("MAINTENANCE");
  await page.getByLabel("Lý do").fill("Bọc lại bìa");
  await page.getByRole("button", { name: "Lưu trạng thái" }).click();
  await expect(page.getByRole("cell", { name: "Bảo trì" }).first()).toBeVisible();
  await page.getByRole("row").filter({ hasText: "Bảo trì" }).first().getByRole("button").click();
  await page.getByLabel("Trạng thái mới").selectOption("AVAILABLE");
  await page.getByRole("button", { name: "Lưu trạng thái" }).click();
  await expect(page.getByText("Đã đổi trạng thái bản sách.")).toBeVisible();
});

test("new categories hang below A/B/C (QĐ04) and search finds authors (YC#1)", async ({ page }) => {
  const name = `Nhánh A.1 ${Date.now().toString(36)}`;
  await page.goto("/staff/catalog/categories");
  await page.getByLabel("Tên", { exact: true }).fill(name);
  await page.getByLabel("Mã thể loại").fill(`A1-${Date.now().toString(36).slice(-5)}`);
  await page.getByLabel(/Thuộc thể loại/).selectOption({ label: "A · Thể loại A" });
  await page.getByRole("button", { name: "Lưu thông tin" }).click();
  await expect(page.getByRole("cell", { name })).toBeVisible();
  await page.goto("/staff/catalog");
  await page.getByLabel("Tìm sách").fill("Nguyễn Nhật Ánh");
  await expect(page.getByRole("cell", { name: "Mắt biếc" })).toBeVisible();
  await page.getByLabel("Tìm sách").fill("zzqq-khong-co-sach");
  await expect(page.getByText("Không tìm thấy")).toBeVisible();
});

test("Ctrl+K finds a screen and a reader (YC#18)", async ({ page }) => {
  await page.goto("/staff/dashboard");
  await expect(page.getByRole("button", { name: /Tìm sách, độc giả, chức năng/ })).toBeVisible();
  await page.keyboard.press("Control+k");
  const box = page.getByRole("combobox", { name: /Từ khóa/ });
  await box.fill("muon sach");
  await expect(page.getByRole("option", { name: /Quầy mượn sách/ })).toBeVisible();
  await box.fill("DG0003");
  await expect(page.getByRole("option", { name: /Lê Quốc Bảo/ })).toBeVisible();
  await page.keyboard.press("Enter");
  await expect(page).toHaveURL(/\/staff\/readers\//);
});
