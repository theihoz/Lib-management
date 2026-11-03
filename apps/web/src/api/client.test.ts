import { createApiClient } from "./client";
import { ApiError, toFieldErrors } from "./errors";
import { createIdempotencyKey } from "./idempotency";
import { formatVnd } from "../lib/money";
import { formatDateTime } from "../lib/datetime";

describe("API boundary", () => {
  it("sends a bearer token and valid request id to the configured API", async () => {
    let received: Request | undefined;
    const api = createApiClient({ baseUrl: "https://library.test", getToken: () => Promise.resolve("token"), fetch: (request) => {
      received = request;
      return Promise.resolve(Response.json({ status: "ready" }));
    } });
    const result = await api.GET("/health/ready");
    expect(result.data).toEqual({ status: "ready" });
    expect(received?.url).toBe("https://library.test/health/ready");
    expect(received?.headers.get("Authorization")).toBe("Bearer token");
    expect(received?.headers.get("X-Request-ID")).toMatch(/^[A-Za-z0-9-]{8,100}$/);
  });
  it("handles a non-JSON gateway response without leaking HTML to users", async () => {
    const api = createApiClient({ fetch: () => Promise.resolve(new Response("<html>upstream failed</html>", { status: 502, headers: { "X-Request-ID": "request-123" } })) });
    await expect(api.GET("/health/ready")).rejects.toMatchObject({ status: 502, code: "INTERNAL_ERROR", requestId: "request-123" });
  });
  it("refreshes only once, then expires a rejected session", async () => {
    let calls = 0;
    let refreshes = 0;
    let expired = false;
    const api = createApiClient({ refresh: () => { refreshes++; return Promise.resolve(true); }, onExpired: () => { expired = true; }, fetch: () => {
      calls++;
      return Promise.resolve(Response.json({ code: "INVALID_TOKEN", message: "Phiên hết hạn", request_id: "request-456" }, { status: 401 }));
    } });
    await expect(api.GET("/api/v1/auth/me")).rejects.toBeInstanceOf(ApiError);
    expect([calls, refreshes, expired]).toEqual([2, 1, true]);
  });
  it("turns a failed connection into a retriable network error", async () => {
    const api = createApiClient({ fetch: () => Promise.reject(new TypeError("connection refused")) });
    await expect(api.GET("/health/ready")).rejects.toMatchObject({ code: "NETWORK_ERROR", status: 0 });
  });
  it("maps validation field paths and ignores unsafe property names", () => {
    expect(toFieldErrors([{ loc: ["body", "email"], msg: "Email sai" }, { loc: ["body", "__proto__"], msg: "unsafe" }])).toEqual({ email: "Email sai" });
  });
  it("keeps a command key across retries and resets it when its payload changes", () => {
    const key = createIdempotencyKey();
    const first = key.forPayload({ readerId: "one", copyIds: ["a"] });
    expect(key.forPayload({ copyIds: ["a"], readerId: "one" })).toBe(first);
    expect(key.forPayload({ readerId: "one", copyIds: ["b"] })).not.toBe(first);
    key.reset();
    expect(key.forPayload({ readerId: "one", copyIds: ["b"] })).not.toBe(first);
  });
  it("formats large VND amounts without losing digits", () => {
    expect(formatVnd("12345678901234567890")).toBe("12.345.678.901.234.567.890 ₫");
    expect(formatDateTime("2026-11-03T17:30:00Z")).toContain("04/11/2026");
  });
});
