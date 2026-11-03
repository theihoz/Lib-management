import { Link } from "react-router";
import { useSession } from "../auth/session";
import { canAccess } from "../auth/session-state";
import { screens } from "../app/screens";
import { Badge, Button, Panel } from "../ui/components";

const PERMISSION_GROUPS: [string, string][] = [
  ["catalog.", "Danh mục"],
  ["reader.", "Độc giả"],
  ["card.", "Thẻ"],
  ["loan.", "Mượn / gia hạn"],
  ["return.", "Trả sách"],
  ["assessment.", "Đánh giá phí"],
  ["payment.", "Thu tiền"],
  ["charge.", "Phí"],
  ["finance.", "Tài chính"],
  ["ledger.", "Sổ cái"],
  ["overdue.", "Quá hạn"],
  ["report.", "Báo cáo"],
  ["export.", "Xuất dữ liệu"],
  ["policy.", "Quy định"],
];

/** Account summary, shortcuts the account may use, and its permissions grouped by area. */
export function MePage({ onLogout }: { onLogout: () => void }) {
  const session = useSession();
  const shortcuts = screens.filter(
    (item) =>
      !item.path.includes(":") &&
      item.permission &&
      item.permission !== "session" &&
      canAccess(session.status, session.permissions, item.permission),
  );
  const grouped = PERMISSION_GROUPS.map(([prefix, label]) => ({
    label,
    codes: session.permissions.filter((code) => code.startsWith(prefix)),
  })).filter((group) => group.codes.length);
  return (
    <div className="stack">
      <Panel title="Tài khoản">
        <dl className="detail-list">
          <div>
            <dt>Tên hiển thị</dt>
            <dd>{session.account?.display_name ?? "—"}</dd>
          </div>
          <div>
            <dt>Trạng thái</dt>
            <dd>
              <Badge tone={session.account?.status === "ACTIVE" ? "success" : "warning"}>
                {session.account?.status === "ACTIVE" ? "Đang hoạt động" : session.account?.status}
              </Badge>
            </dd>
          </div>
          <div>
            <dt>Hồ sơ độc giả</dt>
            <dd>{session.account?.reader_id ? "Đã liên kết" : "Chưa liên kết (tài khoản nhân viên)"}</dd>
          </div>
        </dl>
        <div className="actions">
          <Button variant="secondary" icon="logout" onClick={onLogout}>
            Đăng xuất
          </Button>
        </div>
      </Panel>
      <Panel title="Lối tắt công việc" subtitle="Chỉ hiển thị chức năng tài khoản này được phép dùng.">
        {shortcuts.length ? (
          <ul className="shortcut-list">
            {shortcuts.map((item) => (
              <li key={item.id}>
                <Link to={item.path}>{item.title}</Link>
              </li>
            ))}
          </ul>
        ) : (
          <p className="muted">
            Tài khoản này chưa có chức năng nghiệp vụ. Bạn có thể{" "}
            <Link to="/catalog">tìm sách trong danh mục</Link>.
          </p>
        )}
      </Panel>
      <Panel title="Quyền hiện tại" subtitle="Do máy chủ xác định; giao diện chỉ phản ánh.">
        {grouped.length ? (
          <dl className="detail-list">
            {grouped.map((group) => (
              <div key={group.label}>
                <dt>{group.label}</dt>
                <dd>{group.codes.join(", ")}</dd>
              </div>
            ))}
          </dl>
        ) : (
          <p className="muted">Không có quyền nghiệp vụ ngoài tra cứu danh mục.</p>
        )}
      </Panel>
    </div>
  );
}
