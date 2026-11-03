import { ApiError } from "../api/errors";
import { classifySessionError, canAccess } from "./session-state";

describe("server-derived session permissions", () => {
  it("keeps locked and unlinked accounts out of staff content", () => {
    expect(classifySessionError(new ApiError(403, "ACCOUNT_INACTIVE", "locked"))).toBe("inactive");
    expect(classifySessionError(new ApiError(403, "ACCOUNT_NOT_LINKED", "unlinked"))).toBe("not_linked");
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
});
