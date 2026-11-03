import { useState } from "react";
import type { ReactNode } from "react";
import { Button, Dialog, Field, Notice, Panel, Table } from "../ui/components";
import type { ViewProps } from "./types";

export function PreviewAction({ preview, children, icon, receipt, navigate, variant = "primary" }: { preview?: boolean; children: ReactNode; icon?: string; receipt?: string; navigate?: ViewProps["navigate"]; variant?: "primary" | "secondary" | "danger" }) {
  const [open, setOpen] = useState(false);
  return <><Button variant={variant} icon={icon} disabled={!preview} onClick={() => setOpen(true)} title={preview ? undefined : "Chức năng chưa khả dụng"}>{children}</Button><Dialog open={open} title="Xem lại thao tác" onClose={() => setOpen(false)}><Notice>Đây là bản xem trước giao diện, không ghi dữ liệu vào hệ thống.</Notice><p>Bạn có thể kiểm tra bố cục và nội dung biểu mẫu. Kết quả nghiệp vụ sẽ do hệ thống xác nhận khi chức năng sẵn sàng.</p><div className="actions">{receipt && navigate && <Button onClick={() => { setOpen(false); navigate(receipt); }}>Xem mẫu biên nhận</Button>}<Button variant="secondary" onClick={() => setOpen(false)}>Quay lại</Button></div></Dialog></>;
}
export function FormView({ screen, preview, sample }: ViewProps) {
  const [open, setOpen] = useState(false);
  const labels = screen.fields ?? [];
  return <><Panel title="Thông tin cần ghi nhận" subtitle="Kiểm tra thông tin trước khi xác nhận."><form onSubmit={(event) => { event.preventDefault(); if (preview) setOpen(true); }}><div className="form-grid">{labels.map((label) => <Field label={label} key={label} defaultValue={sample?.values?.[label] ?? ""} required placeholder={`Nhập ${label.toLowerCase()}`} type={label.toLowerCase().includes("email") ? "email" : "text"} />)}</div><div className="actions"><Button type="submit" disabled={!preview}>{screen.action ?? "Lưu thông tin"}</Button><Button variant="secondary" type="reset">Đặt lại</Button></div></form></Panel><Dialog open={open} title="Xem lại thông tin" onClose={() => setOpen(false)}><Notice>Đây là bản xem trước giao diện, không ghi dữ liệu vào hệ thống.</Notice><p>Các giá trị biểu mẫu chỉ tồn tại trong trang hiện tại.</p><Button variant="secondary" onClick={() => setOpen(false)}>Quay lại biểu mẫu</Button></Dialog></>;
}
const nextScreens: Record<string, string> = { "FE02.03": "FE02.04", "FE02.05": "FE02.09", "FE03.01": "FE03.03", "FE04.04": "FE04.01", "FE06.01": "FE06.02", "FE07.03": "FE07.04", "FE09.02": "FE09.03", "FE09.05": "FE09.06", "FE10.01": "FE03.05", "FE10.03": "FE10.04", "FE10.07": "FE10.08", "FE11.01": "FE11.02", "FE11.03": "FE11.02", "FE11.04": "FE11.05" };
const detailScreens: Record<string, string> = { "FE02.03": "FE02.02", "FE03.01": "FE03.02", "FE04.04": "FE04.05", "FE06.01": "FE06.02", "FE07.03": "FE07.04", "FE09.01": "FE04.05", "FE09.05": "FE09.06", "FE10.03": "FE10.05", "FE11.01": "FE11.02", "FE11.04": "FE11.05" };
export function ListView({ screen, preview, sample, navigate }: ViewProps) {
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState("");
  const [page, setPage] = useState(0);
  const all = sample?.rows ?? [];
  const normalized = (value: string) => value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase("vi");
  const filtered = all.filter((row) => normalized(row.join(" ")).includes(normalized(query)) && (!filter || row.includes(filter)));
  const rows = filtered.slice(page * 10, page * 10 + 10);
  const statuses = [...new Set(all.map((row) => row.at(-1)).filter((item): item is string => !!item))];
  return <><div className="toolbar"><Field label="Tìm kiếm" type="search" placeholder="Tên, mã hoặc nội dung liên quan…" value={query} onChange={(event) => { setQuery(event.target.value); setPage(0); }} /><div className="field"><label htmlFor={`filter-${screen.id}`}>Trạng thái</label><select id={`filter-${screen.id}`} value={filter} onChange={(event) => { setFilter(event.target.value); setPage(0); }}><option value="">Tất cả trạng thái</option>{statuses.map((status) => <option key={status}>{status}</option>)}</select></div>{screen.action && (preview && nextScreens[screen.id] && navigate ? <Button icon="plus" onClick={() => navigate(nextScreens[screen.id]!)}>{screen.action}</Button> : <PreviewAction preview={preview}>{screen.action}</PreviewAction>)}</div><Panel className="table-panel"><Table headers={screen.headers ?? ["Mã", "Tên", "Trạng thái"]} rows={rows} caption={screen.title} onRow={preview && navigate && detailScreens[screen.id] ? () => navigate(detailScreens[screen.id]!) : undefined} /><div className="pagination"><span className="muted">Hiển thị {filtered.length ? page * 10 + 1 : 0}–{Math.min((page + 1) * 10, filtered.length)} / {filtered.length} mục</span><div className="actions"><Button variant="secondary" disabled={page === 0} onClick={() => setPage(page - 1)}>Trước</Button><Button variant="secondary" disabled={(page + 1) * 10 >= filtered.length} onClick={() => setPage(page + 1)}>Sau</Button></div></div></Panel>{screen.fields && <Panel title="Thông tin danh mục"><div className="form-grid">{screen.fields.map((label) => <Field key={label} label={label} defaultValue={sample?.values?.[label] ?? ""} />)}</div><div className="actions"><PreviewAction preview={preview}>Lưu thông tin</PreviewAction></div></Panel>}</>;
}
export function ReceiptView({ screen, sample, preview }: ViewProps) {
  return <Panel className="receipt"><div className="receipt-mark">✓</div><span className="eyebrow">{preview ? "Mẫu biên nhận" : "Biên nhận"}</span><h2>{sample?.receipt ?? "Chưa có biên nhận"}</h2><p className="muted">{screen.title}</p>{sample?.items?.length ? <Table headers={["Mã", "Nội dung", "Kết quả"]} rows={sample.items} caption="Chi tiết biên nhận" /> : <Notice>Biên nhận chỉ hiển thị sau khi hệ thống xác nhận thao tác.</Notice>}<div className="actions"><Button variant="secondary" icon="print" disabled={!sample?.receipt} onClick={() => window.print()}>In biên nhận{preview ? " mẫu" : ""}</Button></div></Panel>;
}
