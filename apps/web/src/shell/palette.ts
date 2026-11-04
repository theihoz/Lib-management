// Pure helpers for the Ctrl+K command palette (YC#18).
import type { ScreenDefinition } from "../features/types";

/** Lower-case, accent-free text so "muon sach" finds "Mượn sách". */
export function fold(text: string): string {
  return text
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .replace(/đ/g, "d")
    .replace(/Đ/g, "D")
    .toLowerCase()
    .trim();
}

/** Screens whose title contains every word of the keyword; blank finds nothing (QĐ23). */
export function matchScreens(keyword: string, screens: ScreenDefinition[], limit = 6) {
  const words = fold(keyword).split(/\s+/).filter(Boolean);
  if (!words.length) return [];
  return screens
    .filter((screen) => {
      const title = fold(screen.title);
      return words.every((word) => title.includes(word));
    })
    .slice(0, limit);
}

export function isPaletteShortcut(event: Pick<KeyboardEvent, "key" | "ctrlKey" | "metaKey">) {
  return (event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k";
}
