import { useEffect, useId, useRef, useState } from "react";
import type { ReactNode } from "react";
import { Link, NavLink } from "react-router";
import { screens } from "../app/screens";
import { PageTitleContext, useDocumentTitle, useLibraryName } from "../app/brand";
import type { ScreenDefinition } from "../features/types";
import { Button, Dialog } from "../ui/components";
import { Icon } from "../ui/Icon";
import { formatDateTime } from "../lib/datetime";
import { findNavItem, resolveNavigation } from "./navigation";
import type { ResolvedSection } from "./navigation";

type Props = {
  screen: ScreenDefinition;
  children: ReactNode;
  accountName?: string;
  /** Accounts with only reader permissions get the portal navigation. */
  portal?: boolean;
  /** The API health check failed; data on screen may be stale. */
  offline?: boolean;
  onRetry?: () => void;
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
  portal = false,
  offline = false,
  onRetry,
  onLogin,
  onLogout,
  allowed = () => true,
  topbarExtra,
}: Props) {
  const [drawer, setDrawer] = useState(false);
  const [logout, setLogout] = useState(false);
  const heading = useRef<HTMLHeadingElement>(null);
  const [titleOverride, setTitleOverride] = useState<string>();
  const title = titleOverride ?? screen.title;
  const sections = resolveNavigation(screens, allowed, portal);
  const current = findNavItem(sections, screen.id);
  const isDetail = current?.item.details?.includes(screen.id) ?? false;
  const tabs = current && !isDetail ? current.item.allowedTabs : [];
  useDocumentTitle(title);
  useEffect(() => {
    heading.current?.focus();
  }, [screen.id]);
  const closeDrawer = () => setDrawer(false);
  return (
    <div className={`app-shell ${portal || !accountName ? "portal-shell" : ""}`}>
      <a className="skip-link" href="#main-content">
        Bỏ qua tới nội dung
      </a>
      <aside className="sidebar">
        <SidebarContent
          sections={sections}
          activeKey={current?.item.key}
          onNavigate={closeDrawer}
        />
      </aside>
      <Dialog open={drawer} title="Điều hướng" onClose={closeDrawer}>
        <div className="mobile-navigation">
          <SidebarContent
            sections={sections}
            activeKey={current?.item.key}
            onNavigate={closeDrawer}
          />
        </div>
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
          <div className="topbar-search">{topbarExtra}</div>
          <div className="topbar-actions">
            <span className="topbar-date">{formatDateTime(new Date().toISOString(), true)}</span>
            {onLogout && accountName ? (
              <AccountMenu name={accountName} onLogout={() => setLogout(true)} />
            ) : onLogin ? (
              <Button variant="secondary" icon="key" onClick={onLogin}>
                Đăng nhập
              </Button>
            ) : null}
          </div>
        </header>
        {offline && (
          <div className="connection-banner" role="alert">
            <Icon name="offline" size={18} />
            <span>
              Không kết nối được máy chủ thư viện. Dữ liệu trên màn hình có thể chưa cập nhật.
            </span>
            {onRetry && (
              <Button variant="ghost" icon="refresh" onClick={onRetry}>
                Thử lại
              </Button>
            )}
          </div>
        )}
        <main id="main-content" className="main-content">
          <header className="page-header">
            {isDetail && current ? (
              <Link className="back-link" to={current.item.to}>
                <Icon name="back" size={16} />
                {current.item.label}
              </Link>
            ) : (
              current?.section.label && <span className="eyebrow">{current.section.label}</span>
            )}
            <h1 ref={heading} tabIndex={-1}>
              {title}
            </h1>
          </header>
          {tabs.length > 1 && (
            <nav className="subnav" aria-label={current?.item.label}>
              {tabs.map((tab) => (
                <NavLink key={tab.id} to={tab.to} end>
                  {tab.label}
                </NavLink>
              ))}
            </nav>
          )}
          <PageTitleContext.Provider value={setTitleOverride}>
            <div className="page-enter" key={screen.id}>
              {children}
            </div>
          </PageTitleContext.Provider>
        </main>
        <MobileBar
          sections={sections}
          activeKey={current?.item.key}
          onMore={() => setDrawer(true)}
        />
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

function Brand({ onNavigate }: { onNavigate?: () => void }) {
  const library = useLibraryName();
  return (
    <Link className="brand" to="/" onClick={onNavigate}>
      <span className="brand-mark">
        <Icon name="book" size={20} />
      </span>
      <span className="brand-name">{library}</span>
    </Link>
  );
}

function SidebarContent({
  sections,
  activeKey,
  onNavigate,
}: {
  sections: ResolvedSection[];
  activeKey?: string;
  onNavigate: () => void;
}) {
  return (
    <>
      <Brand onNavigate={onNavigate} />
      <nav aria-label="Điều hướng chính" className="nav">
        {sections.map((section, index) => (
          <div className="nav-section" key={section.label ?? index}>
            {section.label && <span className="nav-section-label">{section.label}</span>}
            {section.items.map((item) => (
              <Link
                key={item.key}
                to={item.to}
                onClick={onNavigate}
                className={`nav-item ${item.key === activeKey ? "nav-active" : ""}`}
                aria-current={item.key === activeKey ? "page" : undefined}
              >
                <Icon name={item.icon} size={18} />
                <span>{item.label}</span>
              </Link>
            ))}
          </div>
        ))}
      </nav>
    </>
  );
}

function AccountMenu({ name, onLogout }: { name: string; onLogout: () => void }) {
  const [open, setOpen] = useState(false);
  const menuId = useId();
  const root = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!open) return;
    const onPointer = (event: PointerEvent) => {
      if (!root.current?.contains(event.target as Node)) setOpen(false);
    };
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };
    document.addEventListener("pointerdown", onPointer);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("pointerdown", onPointer);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);
  return (
    <div className="account-menu" ref={root}>
      <button
        type="button"
        className="account-trigger"
        aria-expanded={open}
        aria-controls={menuId}
        aria-label={`Tài khoản: ${name}`}
        onClick={() => setOpen((value) => !value)}
      >
        <span className="avatar" aria-hidden="true">
          {name.slice(0, 1).toLocaleUpperCase("vi")}
        </span>
        <span className="account-name">{name}</span>
        <Icon name="down" size={16} />
      </button>
      {open && (
        <div className="account-popover" id={menuId}>
          <Link to="/me" onClick={() => setOpen(false)}>
            <Icon name="user" size={18} />
            Tài khoản của tôi
          </Link>
          <button
            type="button"
            onClick={() => {
              setOpen(false);
              onLogout();
            }}
          >
            <Icon name="logout" size={18} />
            Đăng xuất
          </button>
        </div>
      )}
    </div>
  );
}

const MOBILE_KEYS = ["checkout", "returns", "catalog", "me", "dashboard"];
function MobileBar({
  sections,
  activeKey,
  onMore,
}: {
  sections: ResolvedSection[];
  activeKey?: string;
  onMore: () => void;
}) {
  const items = sections
    .flatMap((section) => section.items)
    .filter((item) => MOBILE_KEYS.includes(item.key))
    .sort((a, b) => MOBILE_KEYS.indexOf(a.key) - MOBILE_KEYS.indexOf(b.key))
    .slice(0, 3);
  return (
    <nav className="mobile-bottom" aria-label="Truy cập nhanh">
      {items.map((item) => (
        <Link
          key={item.key}
          to={item.to}
          className={item.key === activeKey ? "is-active" : undefined}
          aria-current={item.key === activeKey ? "page" : undefined}
        >
          <Icon name={item.icon} size={20} />
          {item.shortLabel ?? item.label}
        </Link>
      ))}
      <button type="button" onClick={onMore}>
        <Icon name="menu" size={20} />
        Thêm
      </button>
    </nav>
  );
}
