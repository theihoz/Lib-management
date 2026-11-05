import { Link, useNavigate } from "react-router";
import { useSession } from "../auth/session";
import type { SessionStatus } from "../auth/session-state";
import { useDocumentTitle, useLibraryName } from "../app/brand";
import { Button, Notice } from "../ui/components";
import { Icon } from "../ui/Icon";
import { ApiError } from "../api/errors";

const messages: Record<SessionStatus, [string, string]> = {
  anonymous: [
    "Đăng nhập",
    "Dùng tài khoản thư viện được cấp cho bạn để mượn, gia hạn và theo dõi sách.",
  ],
  checking: ["Đang xác minh phiên", "Vui lòng chờ trong giây lát."],
  authenticated: [
    "Đăng xuất khỏi thư viện?",
    "Bạn sẽ kết thúc phiên làm việc trên trình duyệt này.",
  ],
  expired: [
    "Phiên đăng nhập đã hết hạn",
    "Đăng nhập lại để tiếp tục. Dữ liệu chưa gửi trên biểu mẫu vẫn được giữ.",
  ],
  inactive: ["Tài khoản đã bị khóa", "Liên hệ quầy thư viện hoặc quản trị viên để được hỗ trợ."],
  not_linked: [
    "Tài khoản chưa được liên kết",
    "Tài khoản của bạn chưa gắn với hồ sơ độc giả. Liên hệ quầy thư viện để được liên kết.",
  ],
  offline: ["Không thể kết nối", "Kiểm tra kết nối mạng rồi thử lại."],
};
const stateIcon: Partial<Record<SessionStatus, string>> = {
  checking: "clock",
  expired: "clock",
  inactive: "alert",
  not_linked: "users",
  offline: "offline",
  authenticated: "logout",
};

export function SessionPage() {
  const session = useSession();
  const navigate = useNavigate();
  const library = useLibraryName();
  const [title, description] = messages[session.status];
  useDocumentTitle(title);
  return (
    <div className="auth-page">
      <aside className="auth-aside">
        <Link className="brand" to="/">
          <span className="brand-mark">
            <Icon name="book" size={20} />
          </span>
          <span className="brand-name">{library}</span>
        </Link>
        <p className="auth-quote">
          Một tài khoản.
          <br />
          <em>Cả thư viện.</em>
        </p>
        <p className="auth-tagline">Tra cứu sách, mượn trả và theo dõi tài khoản ở cùng một nơi.</p>
      </aside>
      <main className="auth-main" id="main-content">
        <div className="auth-card">
          {stateIcon[session.status] && (
            <span className={`auth-state auth-state-${session.status}`}>
              <Icon name={stateIcon[session.status]!} size={22} />
            </span>
          )}
          <h1 tabIndex={-1}>{title}</h1>
          <p className="muted">{description}</p>
          <div className="auth-actions">
            {session.status === "authenticated" ? (
              <>
                <Button
                  icon="logout"
                  onClick={() => {
                    void session.logout().then(() => navigate("/login"));
                  }}
                >
                  Xác nhận đăng xuất
                </Button>
                <Button variant="secondary" onClick={() => void navigate("/")}>
                  Ở lại
                </Button>
              </>
            ) : session.status === "offline" ? (
              <Button icon="refresh" onClick={session.retry}>
                Thử lại
              </Button>
            ) : session.personas ? (
              <fieldset className="persona-picker" disabled={session.status === "checking"}>
                <legend>Chọn vai trò (môi trường phát triển)</legend>
                {session.personas.map((persona) => (
                  <Button
                    key={persona.code}
                    variant="secondary"
                    onClick={() => {
                      void session.login(persona.code).then(() => navigate("/"));
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
                  ["inactive", "not_linked"].includes(session.status)
                }
                icon="key"
                onClick={() => {
                  void session.login();
                }}
              >
                {session.status === "checking"
                  ? "Đang xác minh…"
                  : "Đăng nhập bằng tài khoản thư viện"}
              </Button>
            )}
          </div>
          {session.error instanceof ApiError && session.error.requestId && (
            <Notice tone="warning">Mã hỗ trợ: {session.error.requestId}</Notice>
          )}
          <p className="auth-footnote">
            <Link to="/catalog">Xem danh mục sách</Link> không cần đăng nhập.
          </p>
        </div>
      </main>
    </div>
  );
}
