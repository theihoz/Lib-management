// Demo-only module; must never reach a production bundle (CI greps for this marker).
export const MOCK_MARKER = "__LIB_MOCK__";

// Copied from ROLES in apps/api/src/lib_management/identity/rbac_seed.py on 2026-11-03.
const ROLES: Record<string, readonly string[]> = {
  READER: [
    "catalog.read",
    "reader.read",
    "eligibility.read",
    "reservation.read",
    "reservation.create",
    "reservation.cancel",
    "finance.read",
    "notification.read",
    "preference.write",
  ],
  LIBRARIAN: [
    "catalog.read",
    "catalog.write",
    "media.write",
    "reader.read",
    "reader.write",
    "card.issue",
    "eligibility.read",
    "loan.checkout",
    "return.create",
    "loan.renew",
    "reservation.read",
    "reservation.create",
    "reservation.cancel",
    "reservation.pickup",
    "finance.read",
    "assessment.propose",
    "payment.collect",
    "report.read",
    "overdue.read",
    "account.provision_reader",
    "acquisition.write",
  ],
  MANAGER: [
    "catalog.read",
    "reader.read",
    "eligibility.read",
    "finance.read",
    "assessment.decide",
    "charge.waive",
    "ledger.reverse",
    "report.read",
    "overdue.read",
    "export.create",
    "export.download",
    "policy.write",
    "policy.approve",
    "acquisition.approve",
    "copy.dispose",
  ],
  SYSTEM_ADMIN: ["catalog.read", "account.provision_reader", "account.manage", "role.manage"],
  OPS_ADMIN: [
    "catalog.read",
    "backup.create",
    "restore.request",
    "restore.approve",
    "job.read",
    "job.replay",
  ],
};

export type Persona = {
  code: string;
  label: string;
  displayName: string;
  permissions: readonly string[];
  /** Error code /auth/me answers with instead of a session. */
  failure?: "ACCOUNT_NOT_LINKED" | "ACCOUNT_INACTIVE";
};

export const personas: Persona[] = [
  { code: "READER", label: "Độc giả", displayName: "Nguyễn Minh An", permissions: ROLES.READER! },
  {
    code: "LIBRARIAN",
    label: "Thủ thư",
    displayName: "Trần Thu Hà",
    permissions: ROLES.LIBRARIAN!,
  },
  { code: "MANAGER", label: "Quản lý", displayName: "Lê Quốc Bảo", permissions: ROLES.MANAGER! },
  {
    code: "SYSTEM_ADMIN",
    label: "Admin hệ thống",
    displayName: "Phạm Gia Huy",
    permissions: ROLES.SYSTEM_ADMIN!,
  },
  {
    code: "OPS_ADMIN",
    label: "Admin vận hành",
    displayName: "Võ Thanh Tâm",
    permissions: ROLES.OPS_ADMIN!,
  },
  {
    code: "NOT_LINKED",
    label: "Chưa liên kết",
    displayName: "Tài khoản chưa liên kết",
    permissions: [],
    failure: "ACCOUNT_NOT_LINKED",
  },
  {
    code: "INACTIVE",
    label: "Tài khoản bị khóa",
    displayName: "Tài khoản bị khóa",
    permissions: [],
    failure: "ACCOUNT_INACTIVE",
  },
];

export const findPersona = (code: string | undefined) => personas.find((p) => p.code === code);
