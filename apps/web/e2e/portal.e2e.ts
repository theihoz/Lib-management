import { expect, test } from "@playwright/test";
import { checkout, login } from "./helpers";

test("a reader renews their own loan and sees history and fines (YC#9, QĐ22)", async ({
  browser,
}) => {
  const desk = await (await browser.newContext()).newPage();
  await login(desk, "librarian.dev");
  await checkout(desk, "DG0001", "DEMO-0012");

  const reader = await (await browser.newContext()).newPage();
  await login(reader, "reader.dev");
  await reader.goto("/me");
  await expect(reader.getByRole("heading", { name: "Thư viện của tôi" })).toBeVisible();
  await reader
    .getByRole("button", { name: /^Gia hạn phiếu/ })
    .first()
    .click();
  await expect(reader.getByText(/Đã gia hạn/)).toBeVisible();
  await expect(reader.getByRole("cell", { name: "1 lần" })).toBeVisible();
  await reader.getByRole("tab", { name: "Lịch sử" }).click();
  await expect(reader.getByRole("table", { name: /Lịch sử/ })).toBeVisible();
  await reader.getByRole("tab", { name: "Phạt của tôi" }).click();
  await expect(reader.getByRole("table", { name: /Khoản phạt/ })).toBeVisible();
});
