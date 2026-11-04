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
// The READER role's grants: on their own they only reach /me data, never staff screens.
const PORTAL_PERMISSIONS = new Set([
  "catalog.read",
  "reader.read",
  "eligibility.read",
  "loan.renew",
  "reservation.read",
  "reservation.create",
  "reservation.cancel",
  "finance.read",
  "notification.read",
  "preference.write",
]);
export function isStaff(permissions: readonly string[]): boolean {
  return permissions.some((permission) => !PORTAL_PERMISSIONS.has(permission));
}
/** canAccess, plus staff/manager screens stay hidden from portal-only accounts. */
export function canOpen(
  status: SessionStatus,
  permissions: readonly string[],
  screen: { path: string; permission?: string },
): boolean {
  const staffOnly = /^\/(staff|manager)(\/|$)/.test(screen.path);
  return canAccess(status, permissions, screen.permission) && (!staffOnly || isStaff(permissions));
}
