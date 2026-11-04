import { ApiError } from "../api/errors";
import { classifySessionError, canAccess, canOpen } from "./session-state";

describe("server-derived session permissions", () => {
  it("keeps locked and unlinked accounts out of staff content", () => {
    expect(classifySessionError(new ApiError(403, "ACCOUNT_INACTIVE", "locked"))).toBe("inactive");
    expect(classifySessionError(new ApiError(403, "ACCOUNT_NOT_LINKED", "unlinked"))).toBe(
      "not_linked",
    );
    expect(classifySessionError(new ApiError(401, "INVALID_TOKEN", "expired"))).toBe("expired");
    expect(classifySessionError(new ApiError(503, "AUTH_UNAVAILABLE", "offline"))).toBe("offline");
  });
  it("requires an authenticated session and the permission returned by auth/me", () => {
    expect(canAccess("anonymous", ["loan.checkout"], "loan.checkout")).toBe(false);
    expect(canAccess("authenticated", [], "loan.checkout")).toBe(false);
    expect(canAccess("authenticated", ["loan.checkout"], "loan.checkout")).toBe(true);
    expect(canAccess("anonymous", [], undefined)).toBe(true);
    expect(canAccess("authenticated", [], "session")).toBe(true);
  });
  it("keeps portal readers out of staff screens that share a permission", () => {
    const reader = ["catalog.read", "reader.read", "finance.read"];
    const staffLoans = { path: "/staff/loans", permission: "reader.read" };
    expect(canOpen("authenticated", reader, staffLoans)).toBe(false);
    expect(canOpen("authenticated", [...reader, "loan.checkout"], staffLoans)).toBe(true);
    expect(canOpen("authenticated", reader, { path: "/me", permission: "session" })).toBe(true);
  });
});
