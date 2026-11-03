import { groups, screens } from "./screens";

// Core 10-week scope: F01–F09, F11–F14, F16, F18–F20. Phase 2 must stay out of the app.
const PHASE_2_GROUPS = ["10", "11"];
const PHASE_2_PATHS = [
  "/me/loans",
  "/me/reservations",
  "/staff/reservations",
  "/staff/acquisitions",
  "/ops",
];

describe("route registry", () => {
  it("has unique ids and paths", () => {
    expect(new Set(screens.map((item) => item.id)).size).toBe(screens.length);
    expect(new Set(screens.map((item) => item.path)).size).toBe(screens.length);
  });
  it("excludes phase 2 modules", () => {
    expect(screens.some((item) => PHASE_2_GROUPS.includes(item.group))).toBe(false);
    expect(groups.some((item) => PHASE_2_GROUPS.includes(item.id))).toBe(false);
    for (const path of PHASE_2_PATHS)
      expect(screens.some((item) => item.path.startsWith(path))).toBe(false);
  });
  it("uses the permission codes from the permission matrix", () => {
    const byId = (id: string) => screens.find((item) => item.id === id)?.permission;
    expect(byId("FE03.03")).toBe("reader.write");
    expect(byId("FE03.04")).toBe("card.issue");
    expect(byId("FE07.02")).toBe("payment.collect");
    expect(byId("FE07.03")).toBe("assessment.decide");
    expect(byId("FE07.05")).toBe("charge.waive");
    expect(byId("FE09.01")).toBe("overdue.read");
    expect(byId("FE09.04")).toBe("export.create");
    expect(byId("FE09.05")).toBe("policy.write");
  });
  it("only references groups that exist", () => {
    const ids = new Set(groups.map((item) => item.id));
    expect(screens.every((item) => ids.has(item.group))).toBe(true);
  });
});
