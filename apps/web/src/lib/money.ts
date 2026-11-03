export function formatVnd(value: string): string {
  if (!/^-?\d+$/.test(value)) return "—";
  return `${new Intl.NumberFormat("vi-VN").format(BigInt(value))} ₫`;
}
