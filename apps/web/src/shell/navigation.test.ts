import { screens } from "../app/screens";
import { canOpen } from "../auth/session-state";
import { findNavItem, navigation, resolveNavigation } from "./navigation";

const as = (permissions: string[]) => (screen: (typeof screens)[number]) =>
  canOpen("authenticated", permissions, screen);
const labels = (sections: ReturnType<typeof resolveNavigation>) =>
  sections.flatMap((section) => section.items.map((item) => item.label));

describe("navigation", () => {
  it("refers only to screens that exist", () => {
    const ids = new Set(screens.map((screen) => screen.id));
    for (const item of navigation.flatMap((section) => section.items)) {
      for (const id of [...item.tabs.map((tab) => tab.id), ...(item.details ?? [])])
        expect(ids.has(id), id).toBe(true);
    }
  });

  it("never lists sign-in or session screens", () => {
    const listed = navigation.flatMap((section) =>
      section.items.flatMap((item) => [...item.tabs.map((tab) => tab.id), ...(item.details ?? [])]),
    );
    expect(listed.filter((id) => id.startsWith("FE01."))).toEqual([]);
  });

  it("gives guests only the catalogue", () => {
    const sections = resolveNavigation(
      screens,
      (screen) => canOpen("anonymous", [], screen),
      false,
    );
    expect(labels(sections)).toEqual(["Khám phá sách"]);
  });

  it("gives readers the catalogue and their own page, never staff work", () => {
    const sections = resolveNavigation(
      screens,
      as(["catalog.read", "loan.renew", "reservation.read", "finance.read"]),
      true,
    );
    expect(labels(sections)).toEqual(["Khám phá sách", "Của tôi"]);
  });

  it("links staff items to their first allowed tab and hides tabs they may not open", () => {
    const sections = resolveNavigation(
      screens,
      as(["reader.read", "finance.read", "overdue.read"]),
      false,
    );
    const finance = sections.flatMap((s) => s.items).find((item) => item.key === "finance");
    expect(finance?.to).toBe("/staff/finance");
    expect(finance?.allowedTabs.map((tab) => tab.label)).toEqual(["Sổ tài chính"]);
    expect(labels(sections)).not.toContain("Của tôi");
  });

  it("keeps the parent item active on detail screens", () => {
    const sections = resolveNavigation(screens, as(["reader.read", "overdue.read"]), false);
    expect(findNavItem(sections, "FE04.05")?.item.key).toBe("loans");
  });
});
