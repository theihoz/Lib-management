import { ApiError } from "../api/errors";
export type SessionStatus =
  "anonymous" | "checking" | "authenticated" | "expired" | "inactive" | "not_linked" | "offline";
export function classifySessionError(error: unknown): SessionStatus {
  if (!(error instanceof ApiError)) return "offline";
  if (error.code === "ACCOUNT_INACTIVE") return "inactive";
  if (error.code === "ACCOUNT_NOT_LINKED") return "not_linked";
  if (error.status === 401) return "expired";
  return "offline";
}
export function canAccess(
  status: SessionStatus,
  permissions: readonly string[],
  permission?: string,
): boolean {
  if (!permission) return true;
  return (
    status === "authenticated" && (permission === "session" || permissions.includes(permission))
  );
}
