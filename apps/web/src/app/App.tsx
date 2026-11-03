import { lazy, Suspense, useState } from "react";
import { BrowserRouter, Navigate, Route, Routes, useNavigate } from "react-router";
import { QueryClient, QueryClientProvider, useQuery } from "@tanstack/react-query";
import type { RuntimeConfig } from "../config/config";
import { ApiError } from "../api/errors";
import { SessionProvider, useSession } from "../auth/session";
import { canAccess } from "../auth/session-state";
import { Shell } from "../shell/Shell";
import { SessionPage } from "../pages/SessionPage";
import { MePage } from "../pages/MePage";
import { screens } from "./screens";
import type { ScreenDefinition } from "../features/types";
import { LoadingSkeleton } from "../features/live/common";
import "../ui/styles.css";

const LiveFeature = lazy(() => import("../features/live/LiveFeature"));
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
  const allowed = (item: ScreenDefinition) =>
    canAccess(session.status, session.permissions, item.permission);
  const hasPermission = canAccess(session.status, session.permissions, screen.permission);
  const authPage = screen.group === "01" || ["FE08.01", "FE08.06"].includes(screen.id);
  return (
    <Shell
      screen={screen}
      ready={health.data?.status === "ready"}
      accountName={session.account?.display_name}
      onLogin={
        session.status === "authenticated"
          ? undefined
          : () => {
              void navigate("/login");
            }
      }
      onLogout={
        session.status === "authenticated"
          ? () => {
              void session.logout();
            }
          : undefined
      }
      allowed={allowed}
    >
      {screen.id === "FE08.01" && session.status === "authenticated" ? (
        <MePage
          onLogout={() => {
            void session.logout();
          }}
        />
      ) : authPage || !hasPermission ? (
        <SessionPage forbidden={!hasPermission && session.status === "authenticated"} />
      ) : (
        <Suspense fallback={<LoadingSkeleton books={screen.kind === "catalog"} />}>
          <LiveFeature screen={screen} />
        </Suspense>
      )}
    </Shell>
  );
}
function StaffHome() {
  const session = useSession();
  if (session.status === "checking") return <LoadingSkeleton />;
  const first = screens.find(
    (item) =>
      !item.path.includes(":") &&
      item.permission &&
      item.permission !== "session" &&
      canAccess(session.status, session.permissions, item.permission),
  );
  return <Navigate to={first?.path ?? "/catalog"} replace />;
}
function ApplicationRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/catalog" replace />} />
      <Route path="/staff" element={<StaffHome />} />
      {screens.map((screen) => (
        <Route
          key={screen.id}
          path={screen.path}
          element={<LivePage screen={screen} />}
        />
      ))}
      <Route
        path="*"
        element={
          <main className="standalone">
            <h1>Không tìm thấy trang</h1>
            <a href={`${import.meta.env.BASE_URL}catalog`}>Về danh mục sách</a>
          </main>
        }
      />
    </Routes>
  );
}
export function App({ config }: { config: RuntimeConfig }) {
  const [client] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 30_000,
            gcTime: 5 * 60_000,
            // Never retry client errors; retry transient network/5xx failures at most twice.
            retry: (count, error) =>
              count < 2 && !(error instanceof ApiError && error.status >= 400 && error.status < 500),
            refetchOnWindowFocus: true,
          },
          mutations: { retry: false },
        },
      }),
  );
  return (
    <QueryClientProvider client={client}>
      <SessionProvider config={config}>
        <BrowserRouter basename={import.meta.env.BASE_URL.replace(/\/$/, "") || "/"}>
          <ApplicationRoutes />
        </BrowserRouter>
      </SessionProvider>
    </QueryClientProvider>
  );
}
