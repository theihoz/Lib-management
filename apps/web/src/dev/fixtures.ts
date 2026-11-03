import raw from "./fixtures.json";
import type { ScreenSample } from "../features/types";

// __LIB_DESIGN_FIXTURES__ — never import this module from a production route.
type Fixture = { id: string; rows?: string[][]; fields?: string[][]; mini?: string[][]; items?: string[][]; receipt?: string; kind: string };
const fixtures = raw as Fixture[];
const books = [
  { id: "BK-0184", title: "Bến không chồng", author: "Dương Hướng", year: "2023", available: 3, color: "sand" },
  { id: "BK-0207", title: "Mùa lá rụng trong vườn", author: "Ma Văn Kháng", year: "2022", available: 1, color: "sage" },
  { id: "BK-0321", title: "Dế Mèn phiêu lưu ký", author: "Tô Hoài", year: "2024", available: 0, color: "clay" },
  { id: "BK-0455", title: "Nỗi buồn chiến tranh", author: "Bảo Ninh", year: "2021", available: 2, color: "sky" },
];
export function fixtureFor(id: string): ScreenSample {
  const fixture = fixtures.find((item) => item.id === id);
  if (!fixture) throw new Error(`Unknown design screen: ${id}`);
  const rows = fixture.rows ?? (["loan", "ownloans", "renew"].includes(fixture.kind)
    ? [["BC-0184-02", "Bến không chồng", "23/10/2026", fixture.kind === "renew" ? "27/10/2026" : "Đang mượn"], ["BC-0207-01", "Mùa lá rụng trong vườn", "23/10/2026", fixture.kind === "renew" ? "27/10/2026" : "Đang mượn"]]
    : fixture.kind === "history" ? [["PM-1024", "19/10/2026", "2 cuốn", "Đang mượn"], ["PM-0987", "01/10/2026", "3 cuốn", "Đã trả"]]
    : ["hold", "ownholds"].includes(fixture.kind) ? [["DC-207", "Bến không chồng", "READY", "22/10/2026 10:00"]]
    : ["finance", "ownfinance", "payment"].includes(fixture.kind) ? [["PH-091", "Quá hạn", "12.000 ₫", "12.000 ₫", "Chưa thu"], ["PH-086", "Quá hạn", "4.000 ₫", "0 ₫", "Đã thanh toán"]]
    : fixture.kind === "acquisition" ? [["BK-0184", "Bến không chồng", "5", "120.000 ₫"], ["BK-0207", "Mùa lá rụng trong vườn", "3", "90.000 ₫"]]
    : []);
  return {
    rows, items: fixture.items, receipt: fixture.receipt, books,
    values: {
      readerName: "Nguyễn Minh An", readerCode: "DG-001", email: "an@example.com", phone: "0900 000 001", card: "Còn hiệu lực", debt: "0 ₫", loan: "PM-1024", barcode: "BC-0184-02", dueAt: "23/10/2026", account: "librarian.dev", amount: "80000", job: "JOB-119", backup: "BKUP-019", checksum: "SHA-256 · Khớp manifest", ...Object.fromEntries((fixture.fields ?? fixture.mini ?? []).filter((item) => item[0]).map(([key, value]) => [key, value ?? ""])),
    },
  };
}
