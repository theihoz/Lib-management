import { loadConfig } from "./config";

const valid = {
  oidcUrl: "http://localhost:8080",
  oidcRealm: "lib-management",
  oidcClientId: "lib-management-web",
  apiBaseUrl: "",
  mock: false,
};

function respond(body: unknown, init?: ResponseInit): typeof fetch {
  const text = typeof body === "string" ? body : JSON.stringify(body);
  return vi.fn(() => Promise.resolve(new Response(text, init)));
}

describe("loadConfig", () => {
  it("accepts a valid config and requests it without cache", async () => {
    const fetchFn = respond(valid);
    const result = await loadConfig(fetchFn);
    expect(result).toEqual({ ok: true, config: valid });
    expect(fetchFn).toHaveBeenCalledWith("/config.json", { cache: "no-store" });
  });

  it("accepts an absolute https apiBaseUrl", async () => {
    const result = await loadConfig(respond({ ...valid, apiBaseUrl: "https://api.example.org" }));
    expect(result.ok).toBe(true);
  });

  it("rejects a missing field and names it", async () => {
    const partial: Partial<typeof valid> = { ...valid };
    delete partial.oidcClientId;
    const result = await loadConfig(respond(partial));
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.issues.join(" ")).toContain("oidcClientId");
  });

  it.each([
    ["not a URL", { oidcUrl: "localhost:8080" }],
    ["non-http scheme", { oidcUrl: "javascript:alert(1)" }],
    ["relative api base", { apiBaseUrl: "/api" }],
    ["string boolean", { mock: "false" }],
    ["unknown key", { clientSecret: "x" }],
  ])("rejects %s", async (_label, patch) => {
    const result = await loadConfig(respond({ ...valid, ...patch }));
    expect(result.ok).toBe(false);
  });

  it("reports HTTP errors", async () => {
    const result = await loadConfig(respond("missing", { status: 404 }));
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.reason).toContain("404");
  });

  it("reports non-JSON bodies", async () => {
    const result = await loadConfig(respond("<html>", { status: 200 }));
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.reason).toContain("JSON");
  });

  it("reports network failures", async () => {
    const fetchFn = vi.fn(() => Promise.reject(new TypeError("Failed to fetch")));
    const result = await loadConfig(fetchFn);
    expect(result.ok).toBe(false);
  });
});
