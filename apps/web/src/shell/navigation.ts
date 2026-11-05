import type { ScreenDefinition } from "../features/types";

export type NavTab = { id: string; label: string };
export type NavItem = {
  key: string;
  label: string;
  icon: string;
  /** First allowed tab is where the sidebar link goes; tabs show when more than one is allowed. */
  tabs: NavTab[];
  /** Detail screens that keep this item active and offer a way back to it. */
  details?: string[];
  /** Shown only to accounts without staff permissions (the reader portal). */
  portalOnly?: boolean;
};
export type NavSection = { label?: string; items: NavItem[] };

export const navigation: NavSection[] = [
  {
    items: [
      { key: "dashboard", label: "Tổng quan", icon: "home", tabs: [{ id: "FE09.00", label: "Tổng quan" }] },
      {
        key: "catalog",
        label: "Khám phá sách",
        icon: "search",
        tabs: [{ id: "FE02.01", label: "Khám phá sách" }],
        details: ["FE02.02"],
      },
      {
        key: "me",
        label: "Của tôi",
        icon: "user",
        tabs: [{ id: "FE08.01", label: "Của tôi" }],
        portalOnly: true,
      },
    ],
  },
  {
    label: "Lưu thông",
    items: [
      { key: "checkout", label: "Mượn sách", icon: "scan", tabs: [{ id: "FE04.01", label: "Mượn sách" }] },
      { key: "returns", label: "Trả sách", icon: "return", tabs: [{ id: "FE05.01", label: "Trả sách" }] },
      { key: "renewals", label: "Gia hạn", icon: "clock", tabs: [{ id: "FE06.04", label: "Gia hạn" }] },
      {
        key: "reservations",
        label: "Đặt trước",
        icon: "bookmark",
        tabs: [{ id: "FE06.02", label: "Đặt trước" }],
      },
      {
        key: "loans",
        label: "Phiếu mượn",
        icon: "file",
        tabs: [{ id: "FE04.04", label: "Phiếu mượn" }],
        details: ["FE04.05"],
      },
      { key: "overdue", label: "Quá hạn", icon: "alert", tabs: [{ id: "FE09.01", label: "Quá hạn" }] },
    ],
  },
  {
    label: "Bạn đọc",
    items: [
      {
        key: "readers",
        label: "Độc giả và thẻ",
        icon: "users",
        tabs: [
          { id: "FE03.01", label: "Danh sách độc giả" },
          { id: "FE03.03", label: "Thêm độc giả" },
          { id: "FE03.04", label: "Cấp thẻ" },
        ],
        details: ["FE03.02"],
      },
      {
        key: "finance",
        label: "Tài chính",
        icon: "wallet",
        tabs: [
          { id: "FE07.01", label: "Sổ tài chính" },
          { id: "FE07.02", label: "Thu tiền" },
          { id: "FE07.03", label: "Phí chờ duyệt" },
          { id: "FE07.05", label: "Miễn / đảo khoản" },
        ],
        details: ["FE07.04"],
      },
    ],
  },
  {
    label: "Kho sách",
    items: [
      {
        key: "collection",
        label: "Ấn bản và bản sách",
        icon: "library",
        tabs: [
          { id: "FE02.03", label: "Ấn bản" },
          { id: "FE02.04", label: "Thêm ấn bản" },
          { id: "FE02.05", label: "Bản sách" },
          { id: "FE02.06", label: "Tác giả" },
          { id: "FE02.07", label: "Nhà xuất bản" },
          { id: "FE02.08", label: "Phân loại" },
        ],
      },
    ],
  },
  {
    label: "Quản lý",
    items: [
      {
        key: "reports",
        label: "Báo cáo",
        icon: "chart",
        tabs: [
          { id: "FE09.02", label: "Báo cáo" },
          { id: "FE09.04", label: "Xuất CSV" },
        ],
        details: ["FE09.03"],
      },
      {
        key: "policies",
        label: "Quy định",
        icon: "settings",
        tabs: [
          { id: "FE09.05", label: "Các phiên bản" },
          { id: "FE09.06", label: "Soạn phiên bản mới" },
        ],
      },
    ],
  },
];

export type ResolvedItem = NavItem & { to: string; allowedTabs: (NavTab & { to: string })[] };
export type ResolvedSection = { label?: string; items: ResolvedItem[] };

/** Sections and items the account may open, each linked to its first allowed screen. */
export function resolveNavigation(
  screens: ScreenDefinition[],
  allowed: (screen: ScreenDefinition) => boolean,
  portal: boolean,
): ResolvedSection[] {
  const byId = new Map(screens.map((screen) => [screen.id, screen]));
  return navigation
    .map((section) => ({
      label: section.label,
      items: section.items.flatMap((item) => {
        if (item.portalOnly && !portal) return [];
        const allowedTabs = item.tabs.flatMap((tab) => {
          const screen = byId.get(tab.id);
          return screen && !screen.path.includes(":") && allowed(screen)
            ? [{ ...tab, to: screen.path }]
            : [];
        });
        return allowedTabs.length ? [{ ...item, to: allowedTabs[0]!.to, allowedTabs }] : [];
      }),
    }))
    .filter((section) => section.items.length > 0);
}

export function findNavItem(sections: ResolvedSection[], screenId: string) {
  for (const section of sections) {
    for (const item of section.items) {
      if (item.tabs.some((tab) => tab.id === screenId) || item.details?.includes(screenId))
        return { section, item };
    }
  }
  return undefined;
}
