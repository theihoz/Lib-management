import { expect, type Page } from "@playwright/test";

export const PASSWORD = process.env.KEYCLOAK_DEV_USER_PASSWORD ?? "";

/** Sign in through the real Keycloak login page (PKCE flow). */
export async function login(page: Page, username: string): Promise<void> {
  expect(PASSWORD, "set KEYCLOAK_DEV_USER_PASSWORD").not.toBe("");
  await page.goto("/login");
  await page.getByRole("button", { name: /Tiếp tục với SSO/ }).click();
  await page.locator("#username").fill(username);
  await page.locator("#password").fill(PASSWORD);
  await page.locator("#kc-login").click();
  await page.waitForURL(
    (url) => !url.pathname.startsWith("/session") && !url.port.endsWith("8080"),
  );
  await expect(page.getByText("Đã kết nối")).toBeVisible();
}

/** Library-local date (YYYY-MM-DD). */
export function today(): string {
  return new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Ho_Chi_Minh" }).format(new Date());
}

export async function pickReader(page: Page, code: string): Promise<void> {
  await page.getByLabel("Số thẻ, mã hoặc tên độc giả").fill(code);
  await page.getByRole("button", { name: "Tìm độc giả" }).click();
  await page.getByRole("button", { name: code }).click();
}

/** Lend one demo copy to a reader at the counter. */
export async function checkout(page: Page, reader: string, barcode: string): Promise<void> {
  await page.goto("/staff/checkout");
  await pickReader(page, reader);
  await expect(page.getByText("Đủ điều kiện", { exact: true })).toBeVisible();
  await page.getByLabel("Mã vạch bản sách").fill(barcode);
  await page.getByRole("button", { name: "Thêm sách" }).click();
  await expect(page.getByText(barcode, { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Xác nhận mượn sách" }).click();
  await page.getByRole("button", { name: "Xác nhận", exact: true }).click();
  await expect(page.getByText("Biên nhận mượn sách").first()).toBeVisible();
}
