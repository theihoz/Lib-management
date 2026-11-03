export function formatDateTime(value: string, dateOnly = false): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return new Intl.DateTimeFormat("vi-VN", { timeZone: "Asia/Ho_Chi_Minh", day: "2-digit", month: "2-digit", year: "numeric", ...(dateOnly ? {} : { hour: "2-digit", minute: "2-digit" }) }).format(date);
}
