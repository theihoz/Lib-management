import { useEffect, useRef, useState } from "react";
import type { ReactNode } from "react";
import { Link, NavLink } from "react-router";
import { groups, screens } from "../app/screens";
import type { ScreenDefinition } from "../features/types";
import { Badge, Button, Dialog } from "../ui/components";
import { Icon } from "../ui/Icon";
import { formatDateTime } from "../lib/datetime";

type Props = {
  screen: ScreenDefinition;
  children: ReactNode;
  accountName?: string;
  ready?: boolean;
  onLogin?: () => void;
  onLogout?: () => void;
  allowed?: (screen: ScreenDefinition) => boolean;
  /** Extra top-bar controls, e.g. the Ctrl+K palette. */
  topbarExtra?: ReactNode;
};
export function Shell({
  screen,
  children,
  accountName,
  ready,
  onLogin,
  onLogout,
  allowed = () => true,
  topbarExtra,
}: Props) {
  const [drawer, setDrawer] = useState(false);
  const [logout, setLogout] = useState(false);
  const heading = useRef<HTMLHeadingElement>(null);
  const group = groups.find((item) => item.id === screen.group);
  const shown = screens.filter((item) => !item.path.includes(":") && allowed(item));
  const destination = (item: ScreenDefinition) =>
    item.path.includes(":") ? item.path.split("/:")[0]! : item.path;
  useEffect(() => {
    heading.current?.focus();
  }, [screen.id]);
  const navigation = (
    <>
      <Link className="brand" to="/catalog" onClick={() => setDrawer(false)}>
        <span className="brand-icon">
          <Icon name="book" size={25} />
        </span>
        <span>
          LIB / MANAGEMENT<small>THƯ VIỆN ĐƯƠNG ĐẠI</small>
        </span>
      </Link>
      <div className="nav-section-label">KHÔNG GIAN THƯ VIỆN</div>
      <nav aria-label="Điều hướng chính">
        {groups.map((item) => {
          const first = shown.find((entry) => entry.group === item.id);
          if (!first) return null;
          return (
            <NavLink
              key={item.id}
              to={destination(first)}
              onClick={() => setDrawer(false)}
              className={`nav-item ${screen.group === item.id ? "nav-active" : ""}`}
              aria-current={screen.group === item.id ? "page" : undefined}
            >
              <Icon name={item.icon} size={19} />
              <span>{item.title}</span>
              {screen.group === item.id && <Icon name="chevron" size={14} />}
            </NavLink>
          );
        })}
      </nav>
      <div className="sidebar-footer">
        <div className="sidebar-avatar">{accountName?.slice(0, 1).toUpperCase() ?? "K"}</div>
        <div>
          <strong>{accountName ?? "Khách thư viện"}</strong>
          <small>{accountName ? "Phiên làm việc hiện tại" : "Danh mục công khai"}</small>
        </div>
      </div>
    </>
  );
  return (
    <div className={`app-shell ${screen.group === "08" ? "portal-shell" : ""}`}>
      <a className="skip-link" href="#main-content">
        Bỏ qua tới nội dung
      </a>
      <aside className="sidebar">{navigation}</aside>
      <Dialog open={drawer} title="Điều hướng thư viện" onClose={() => setDrawer(false)}>
        <div className="mobile-navigation">{navigation}</div>
      </Dialog>
      <div className="workspace">
        <header className="topbar">
          <Button
            variant="ghost"
            icon="menu"
            aria-label="Mở điều hướng"
            onClick={() => setDrawer(true)}
            className="mobile-menu"
          />
          <span className="topbar-label">Không gian làm việc</span>
          <div className="topbar-actions">
            {topbarExtra}
            <span className="topbar-date">{formatDateTime(new Date().toISOString(), true)}</span>
            <Badge tone={ready ? "success" : "neutral"}>
              {ready ? "Đã kết nối" : "Đang kết nối"}
            </Badge>
            {onLogout ? (
              <Button variant="ghost" icon="logout" onClick={() => setLogout(true)}>
                Đăng xuất
              </Button>
            ) : onLogin ? (
              <Button variant="secondary" icon="key" onClick={onLogin}>
                Đăng nhập
              </Button>
            ) : null}
          </div>
        </header>
        <main id="main-content" className="main-content">
          <div className="breadcrumb">
            <Link to="/catalog">Thư viện</Link>
            <Icon name="chevron" size={13} />
            <span>{group?.title}</span>
          </div>
          <div className="page-heading">
            <div>
              <span className="eyebrow">{group?.title.toLocaleUpperCase("vi")}</span>
              <h1 ref={heading} tabIndex={-1}>
                {screen.title}
              </h1>
            </div>
            <span className="screen-number">{screen.id}</span>
          </div>
          <nav className="subnav" aria-label="Các trang trong nhóm">
            {shown
              .filter((item) => item.group === screen.group)
              .map((item) => (
                <NavLink
                  key={item.id}
                  to={destination(item)}
                  className={screen.id === item.id ? "is-active" : ""}
                  aria-current={screen.id === item.id ? "page" : undefined}
                >
                  {item.title}
                </NavLink>
              ))}
          </nav>
          <div className="page-enter" key={screen.id}>
            {children}
          </div>
          <footer className="page-footer">
            <span>LIB–MANAGEMENT / {screen.id}</span>
            <span>THƯ VIỆN ĐƯƠNG ĐẠI</span>
          </footer>
        </main>
        <nav className="mobile-bottom" aria-label="Truy cập nhanh">
          <Link to="/catalog">
            <Icon name="book" size={20} />
            Tìm sách
          </Link>
          <Link to="/me">
            <Icon name="user" size={20} />
            Của tôi
          </Link>
          <Button variant="ghost" icon="menu" onClick={() => setDrawer(true)}>
            Menu
          </Button>
        </nav>
      </div>
      <Dialog open={logout} title="Đăng xuất khỏi thư viện?" onClose={() => setLogout(false)}>
        <p>Bạn sẽ kết thúc phiên làm việc trên trình duyệt này.</p>
        <div className="actions">
          <Button
            onClick={() => {
              setLogout(false);
              onLogout?.();
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
