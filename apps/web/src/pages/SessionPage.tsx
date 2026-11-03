import { useState } from "react";
import { useNavigate } from "react-router";
import { useSession } from "../auth/session";
import type { SessionStatus } from "../auth/session-state";
import { Badge, Button, Dialog, Notice, Panel } from "../ui/components";
import { Icon } from "../ui/Icon";
import { ApiError } from "../api/errors";

const messages: Record<SessionStatus, [string, string]> = {
  anonymous: ["Đăng nhập thư viện", "Sử dụng tài khoản được nhân viên cấp hoặc liên kết."],
  checking: ["Đang xác minh phiên", "Vui lòng chờ trong khi thư viện kiểm tra phiên đăng nhập."],
  authenticated: ["Tài khoản thư viện", "Thông tin phiên làm việc và quyền truy cập hiện tại."],
  expired: ["Phiên đăng nhập hết hạn", "Đăng nhập lại để tiếp tục làm việc."],
  inactive: ["Tài khoản đã bị khóa", "Liên hệ quản trị viên để kiểm tra trạng thái tài khoản."],
  not_linked: [
    "Tài khoản chưa được liên kết",
    "Liên hệ nhân viên để liên kết tài khoản với hồ sơ thư viện.",
  ],
  offline: [
    "Không thể kết nối",
    "Kiểm tra kết nối mạng hoặc liên hệ nhân viên thư viện rồi thử lại.",
  ],
};
export function SessionPage({ forbidden = false }: { forbidden?: boolean }) {
  const session = useSession();
  const navigate = useNavigate();
  const [logout, setLogout] = useState(false);
  const [title, description] = forbidden
    ? ["Bạn chưa có quyền truy cập", "Tài khoản hiện tại không có quyền thực hiện thao tác này."]
    : messages[session.status];
  return (
    <div className="auth-layout">
      <div className="auth-editorial">
        <span className="eyebrow">LIB / MANAGEMENT</span>
        <Icon name="book" size={64} />
        <h2>
          Một tài khoản.
          <br />
          <em>Cả thư viện.</em>
        </h2>
        <p>
          Không gian cho những cuốn sách,
          <br />
          và những người yêu đọc.
        </p>
      </div>
      <Panel className="auth-card">
        <Badge>TÀI KHOẢN THƯ VIỆN</Badge>
        <h2>{title}</h2>
        <p className="muted">{description}</p>
        {session.status === "authenticated" && !forbidden ? (
          <>
            <dl className="detail-list">
              <div>
                <dt>Tên hiển thị</dt>
                <dd>{session.account?.display_name}</dd>
              </div>
              <div>
                <dt>Trạng thái</dt>
                <dd>{session.account?.status}</dd>
              </div>
              <div>
                <dt>Quyền hiện tại</dt>
                <dd>{session.permissions.length} quyền</dd>
              </div>
            </dl>
            <Button variant="secondary" icon="logout" onClick={() => setLogout(true)}>
              Đăng xuất
            </Button>
          </>
        ) : (
          <div className="actions">
            {session.status === "offline" ? (
              <Button variant="secondary" icon="refresh" onClick={session.retry}>
                Thử lại
              </Button>
            ) : session.personas && !forbidden ? (
              <fieldset className="persona-picker" disabled={session.status === "checking"}>
                <legend>Bản demo: chọn vai trò để đăng nhập</legend>
                {session.personas.map((persona) => (
                  <Button
                    key={persona.code}
                    variant="secondary"
                    icon="key"
                    onClick={() => {
                      void session.login(persona.code).then(() => navigate("/staff"));
                    }}
                  >
                    {persona.label}
                  </Button>
                ))}
              </fieldset>
            ) : (
              <Button
                disabled={
                  session.status === "checking" ||
                  forbidden ||
                  ["inactive", "not_linked"].includes(session.status)
                }
                icon="key"
                onClick={() => {
                  void session.login();
                }}
              >
                {session.status === "checking" ? "Đang xác minh…" : "Tiếp tục với SSO"}
              </Button>
            )}
          </div>
        )}
        {session.error instanceof ApiError && session.error.requestId && (
          <Notice tone="warning">Mã hỗ trợ: {session.error.requestId}</Notice>
        )}
        <p className="muted">Cần hỗ trợ? Liên hệ nhân viên thư viện.</p>
      </Panel>
      <Dialog open={logout} title="Đăng xuất khỏi thư viện?" onClose={() => setLogout(false)}>
        <p>Bạn sẽ kết thúc phiên làm việc trên trình duyệt này.</p>
        <div className="actions">
          <Button
            onClick={() => {
              setLogout(false);
              void session.logout();
            }}
          >
            Xác nhận đăng xuất
          </Button>
          <Button variant="secondary" onClick={() => setLogout(false)}>
            Ở lại
          </Button>
        </div>
      </Dialog>
    </div>
  );
}
