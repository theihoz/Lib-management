import { lazy, Suspense, useState } from "react";
import { BrowserRouter, Link, Navigate, Route, Routes, useNavigate } from "react-router";
import { QueryClient, QueryClientProvider, useQuery } from "@tanstack/react-query";
import type { RuntimeConfig } from "../config/config";
import { ApiError } from "../api/errors";
import { SessionProvider, useSession } from "../auth/session";
import type { DemoMode } from "../auth/session";
import { canOpen, isStaff } from "../auth/session-state";
import type { SessionStatus } from "../auth/session-state";
import { DEFAULT_LIBRARY_NAME, LibraryNameContext, useDocumentTitle } from "./brand";
import { Icon } from "../ui/Icon";
import { Shell } from "../shell/Shell";
import { SessionPage } from "../pages/SessionPage";
import { MePage } from "../pages/MePage";
import { screens } from "./screens";
import type { ScreenDefinition } from "../features/types";
import { LoadingSkeleton } from "../features/live/common";
import "../ui/styles.css";
import { CommandPalette } from "../shell/CommandPalette";

const LiveFeature = lazy(() => import("../features/live/LiveFeature"));

/** Staff land on the dashboard, portal accounts on "Của tôi", guests on the catalogue. */
function homePath(status: SessionStatus, permissions: readonly string[]): string {
  if (status !== "authenticated") return "/catalog";
  if (!isStaff(permissions)) return "/me";
  const dashboard = screens.find((item) => item.id === "FE09.00");
  if (dashboard && canOpen(status, permissions, dashboard)) return dashboard.path;
  const first = screens.find(
    (item) =>
      !item.path.includes(":") &&
      item.permission &&
      item.permission !== "session" &&
      canOpen(status, permissions, item),
  );
  return first?.path ?? "/catalog";
}
function Home() {
  const session = useSession();
  if (!session.initialized || session.status === "checking") return <LoadingSkeleton />;
  return <Navigate to={homePath(session.status, session.permissions)} replace />;
}
function LivePage({ screen }: { screen: ScreenDefinition }) {
  const session = useSession();
  const navigate = useNavigate();
  const health = useQuery({
    queryKey: ["health", "ready"],
    queryFn: async ({ signal }) => (await session.services.health.health_ready({ signal })).data,
    staleTime: 15_000,
    refetchInterval: 30_000,
    retry: 1,
  });
  const allowed = (item: ScreenDefinition) => canOpen(session.status, session.permissions, item);
  const authenticated = session.status === "authenticated";
  const settling = !session.initialized || session.status === "checking";
  if (screen.group === "01") {
    if (authenticated && screen.id !== "FE01.07")
      return <Navigate to={homePath(session.status, session.permissions)} replace />;
    return <SessionPage />;
  }
  if (!allowed(screen) && !authenticated) {
    if (settling) return <LoadingSkeleton />;
    return <SessionPage />;
  }
  return (
    <Shell
      screen={screen}
      portal={authenticated && !isStaff(session.permissions)}
      offline={health.isError || (health.data !== undefined && health.data.status !== "ready")}
      onRetry={() => void health.refetch()}
      accountName={session.account?.display_name}
      onLogin={authenticated ? undefined : () => void navigate("/login")}
      onLogout={authenticated ? () => void session.logout() : undefined}
      allowed={allowed}
      topbarExtra={
        authenticated ? (
          <CommandPalette
            screens={screens.filter((item) => !item.path.includes(":") && allowed(item))}
          />
        ) : undefined
      }
    >
      {!allowed(screen) ? (
        <Forbidden home={homePath(session.status, session.permissions)} />
      ) : screen.id === "FE08.01" ? (
        <MePage onLogout={() => void session.logout()} />
      ) : (
        <Suspense fallback={<LoadingSkeleton books={screen.kind === "catalog"} />}>
          <LiveFeature screen={screen} />
        </Suspense>
      )}
    </Shell>
  );
}
function Forbidden({ home }: { home: string }) {
  return (
    <div className="panel empty-state">
      <Icon name="key" size={30} />
      <h2>Bạn chưa có quyền truy cập trang này</h2>
      <p>Tài khoản hiện tại không được phép dùng chức năng này. Liên hệ quản lý thư viện nếu bạn cần quyền.</p>
      <Link className="button button-secondary" to={home}>
        Về trang chính
      </Link>
    </div>
  );
}
function NotFound() {
  useDocumentTitle("Không tìm thấy trang");
  return (
    <main className="standalone" id="main-content">
      <span className="eyebrow">Lỗi 404</span>
      <h1>Không tìm thấy trang</h1>
      <p className="muted">Đường dẫn có thể đã thay đổi hoặc không còn tồn tại.</p>
      <Link className="button button-primary" to="/">
        Về trang chính
      </Link>
    </main>
  );
}
function ApplicationRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/staff" element={<Home />} />
      {screens.map((screen) => (
        <Route key={screen.id} path={screen.path} element={<LivePage screen={screen} />} />
      ))}
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}
export function App({ config, demo }: { config: RuntimeConfig; demo?: DemoMode }) {
  const [client] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 30_000,
            gcTime: 5 * 60_000,
            // Never retry client errors; retry transient network/5xx failures at most twice.
            retry: (count, error) =>
              count < 2 &&
              !(error instanceof ApiError && error.status >= 400 && error.status < 500),
            refetchOnWindowFocus: true,
          },
          mutations: { retry: false },
        },
      }),
  );
  return (
    <QueryClientProvider client={client}>
      <SessionProvider config={config} demo={demo}>
        <LibraryNameContext.Provider value={config.libraryName ?? DEFAULT_LIBRARY_NAME}>
          {demo && (
            <p className="dev-banner" role="note">
              Môi trường phát triển: dữ liệu giả lập trong trình duyệt.
            </p>
          )}
          <BrowserRouter basename={import.meta.env.BASE_URL.replace(/\/$/, "") || "/"}>
            <ApplicationRoutes />
          </BrowserRouter>
        </LibraryNameContext.Provider>
      </SessionProvider>
    </QueryClientProvider>
  );
}
