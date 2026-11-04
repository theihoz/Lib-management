import { describe, expect, it } from "vitest";
import { DEFAULT_RULES, policyInForce, toDraft, toRules, validateDraft } from "./policyRules";

describe("policy rules v2 (QĐ17)", () => {
  it("round-trips the defaults through the form draft", () => {
    expect(toRules(toDraft(DEFAULT_RULES))).toEqual(DEFAULT_RULES);
    expect(validateDraft(toDraft(DEFAULT_RULES))).toEqual({});
  });

  it("fills keys missing from a v1 policy with defaults", () => {
    const draft = toDraft({ allowedOutstandingBalance: "0", maxBooksPerLoan: 4 });
    expect(draft.allowedOutstandingBalance).toBe("0");
    expect(draft["damageLostFees.LOST"]).toBe("100000");
    expect(draft.libraryName).toBe(DEFAULT_RULES.libraryName);
  });

  it("rejects values the API would reject", () => {
    const draft = toDraft(DEFAULT_RULES);
    const errors = validateDraft({
      ...draft,
      allowedOutstandingBalance: "0",
      overdueFinePerDay: "-1",
      readyHoldDays: "0",
      libraryName: " ",
      "damageLostFees.LOST": "700000",
      minReaderAge: "60",
    });
    expect(Object.keys(errors).sort()).toEqual(
      [
        "allowedOutstandingBalance",
        "damageLostFees.LOST",
        "libraryName",
        "maxReaderAge",
        "overdueFinePerDay",
        "readyHoldDays",
      ].sort(),
    );
  });

  it("finds the policy in force like the API", () => {
    const rows = [
      { status: "DRAFT", effective_from: "2026-01-01T00:00:00Z", rules: {} },
      { status: "ACTIVE", effective_from: "2026-12-01T00:00:00Z", rules: { v: 3 } },
      {
        status: "SUPERSEDED",
        effective_from: "2026-01-01T00:00:00Z",
        effective_to: "2026-12-01T00:00:00Z",
        rules: { v: 2 },
      },
    ];
    expect(policyInForce(rows, Date.parse("2026-11-04T00:00:00Z"))?.rules).toEqual({ v: 2 });
    expect(policyInForce(rows, Date.parse("2026-12-02T00:00:00Z"))?.rules).toEqual({ v: 3 });
  });
});
