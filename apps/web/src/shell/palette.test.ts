import { describe, expect, it } from "vitest";
import type { ScreenDefinition } from "../features/types";
import { fold, isPaletteShortcut, matchScreens } from "./palette";

const screen = (id: string, title: string): ScreenDefinition => ({
  id,
  title,
  group: "04",
  kind: "list",
  path: `/${id}`,
  implemented: true,
});
const screens = [
  screen("a", "Quầy mượn sách"),
  screen("b", "Tiếp nhận trả sách"),
  screen("c", "Độc giả và thẻ"),
];

describe("command palette helpers (YC#18)", () => {
  it("folds Vietnamese accents", () => {
    expect(fold("  Độc GIẢ ")).toBe("doc gia");
  });
  it("matches every word without accents", () => {
    expect(matchScreens("muon sach", screens).map((s) => s.id)).toEqual(["a"]);
    expect(matchScreens("sach", screens).map((s) => s.id)).toEqual(["a", "b"]);
    expect(matchScreens("doc gia", screens).map((s) => s.id)).toEqual(["c"]);
  });
  it("finds nothing for a blank keyword (QĐ23)", () => {
    expect(matchScreens("   ", screens)).toEqual([]);
  });
  it("recognises Ctrl+K and Cmd+K", () => {
    expect(isPaletteShortcut({ key: "k", ctrlKey: true, metaKey: false })).toBe(true);
    expect(isPaletteShortcut({ key: "K", ctrlKey: false, metaKey: true })).toBe(true);
    expect(isPaletteShortcut({ key: "k", ctrlKey: false, metaKey: false })).toBe(false);
  });
});
