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

/** BM02 / YC#6 card status as the desk sees it; "Hết hạn" is derived from expires_at. */
export function cardStatus(card: { status: string; expires_at: string }, now = Date.now()) {
  if (card.status === "REVOKED") return "Đã thu hồi";
  if (card.status === "BLOCKED") return "Tạm khóa";
  return new Date(card.expires_at).getTime() <= now ? "Hết hạn" : "Hoạt động";
}

export const ELIGIBILITY_REASON: Record<string, string> = {
  READER_INACTIVE: "Độc giả không hoạt động",
  CARD_NOT_VALID: "Không có thẻ còn hạn (QĐ02)",
  CARD_BLOCKED: "Thẻ đang tạm khóa",
  OUTSTANDING_BALANCE: "Nợ phạt vượt ngưỡng (QĐ12)",
  OVERDUE_ITEMS: "Đang có sách quá hạn (QĐ08)",
  PENDING_ASSESSMENT: "Có khoản phí chờ Quản lý xác nhận",
};

export function eligibilityReason(code: string): string {
  return ELIGIBILITY_REASON[code] ?? code;
}
