import { expect, test } from "@playwright/test";
import { checkout, login } from "./helpers";

// YC#10 / Lab 2 YC9 / BM04: reserve a book that is out, hand it over after the return.
test("reserve, return, hand over (F10)", async ({ browser }) => {
  const desk = await (await browser.newContext()).newPage();
  await login(desk, "librarian.dev");
  await desk.goto("/staff/catalog");
  await desk.getByLabel("Tìm sách").fill("Kinh tế học vi mô");
  await desk.getByRole("button", { name: "Kinh tế học vi mô", exact: true }).first().click();
  await desk.waitForURL(/\/catalog\/[0-9a-f-]{36}/);
  const edition = desk.url().match(/[0-9a-f-]{36}/)![0];
  await desk.goto(`/staff/catalog/copies?edition=${edition}`);
  const row = desk.getByRole("row").filter({ hasText: "Sẵn sàng" }).first();
  const barcode = (await row.getByRole("button").innerText()).trim();
  await checkout(desk, "DG0002", barcode);

  const reader = await (await browser.newContext()).newPage();
  await login(reader, "reader.dev");
  await reader.goto(`/catalog/${edition}`);
  await reader.getByRole("button", { name: "Đặt trước sách này" }).click();
  await expect(reader.getByText(/Đã đặt trước/)).toBeVisible();

  await desk.goto("/staff/returns");
  await desk.getByLabel("Mã vạch bản sách").fill(barcode);
  await desk.getByRole("button", { name: "Tìm khoản mượn" }).click();
  await desk.getByRole("button", { name: "Ghi nhận trả sách" }).click();
  await expect(desk.getByText("Biên nhận trả sách")).toBeVisible();
  await desk.goto("/staff/reservations");
  await desk
    .getByRole("row")
    .filter({ hasText: "Sẵn sàng nhận" })
    .filter({ hasText: "Kinh tế học vi mô" })
    .first()
    .getByRole("button")
    .click();
  await desk.getByRole("button", { name: "Giao sách" }).click();
  await expect(desk.getByText("Đã cập nhật đặt trước.")).toBeVisible();

  await reader.goto("/me");
  await expect(reader.getByRole("cell", { name: "Kinh tế học vi mô" })).toBeVisible();
});
