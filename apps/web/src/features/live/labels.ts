// Vietnamese labels for stored status codes (YC#2 / D1, BM02).
export const COPY_STATUS: Record<string, string> = {
  AVAILABLE: "Sẵn sàng",
  ON_LOAN: "Đã mượn",
  HELD: "Đang giữ chỗ",
  REPAIR: "Hỏng",
  MAINTENANCE: "Bảo trì",
  LOST: "Mất",
  RETIRED: "Đã thanh lý",
};
/** Statuses staff may set by hand; others change through circulation or disposal. */
export const MANUAL_COPY_STATUS = ["AVAILABLE", "REPAIR", "MAINTENANCE", "LOST"] as const;
export type ManualCopyStatus = (typeof MANUAL_COPY_STATUS)[number];

export function copyStatus(code: string): string {
  return COPY_STATUS[code] ?? code;
}
