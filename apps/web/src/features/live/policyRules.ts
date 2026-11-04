// Policy rules schema v2 (BM09; validated the same way by the API, QĐ17).
export const RULES_SCHEMA_VERSION = 2 as const;

export type DamageLostFees = { MINOR_DAMAGE: string; MAJOR_DAMAGE: string; LOST: string };
export type PolicyRules = {
  libraryName: string;
  minReaderAge: number;
  maxReaderAge: number;
  cardValidityMonths: number;
  maxBooksPerLoan: number;
  initialLoanDays: number;
  maxRenewals: number;
  renewalDays: number;
  overdueFinePerDay: string;
  allowedOutstandingBalance: string;
  publicationYearWindow: number;
  readyHoldDays: number;
  damageLostAssessment: "MANUAL_APPROVAL";
  damageLostFees: DamageLostFees;
};

export const DEFAULT_RULES: PolicyRules = {
  libraryName: "Thư viện Lib-management",
  minReaderAge: 12,
  maxReaderAge: 55,
  cardValidityMonths: 6,
  maxBooksPerLoan: 4,
  initialLoanDays: 4,
  maxRenewals: 1,
  renewalDays: 4,
  overdueFinePerDay: "1000",
  allowedOutstandingBalance: "50000",
  publicationYearWindow: 8,
  readyHoldDays: 3,
  damageLostAssessment: "MANUAL_APPROVAL",
  damageLostFees: { MINOR_DAMAGE: "20000", MAJOR_DAMAGE: "50000", LOST: "100000" },
};

export const LOST_FEE_MIN = 100_000;
export const LOST_FEE_MAX = 600_000;

type Kind = "text" | "int" | "money";
export type RuleField = {
  key: string;
  label: string;
  kind: Kind;
  min: number;
  max?: number;
  source: string;
};

// Flat keys; damage fees use "damageLostFees.<LEVEL>".
export const RULE_FIELDS: RuleField[] = [
  { key: "libraryName", label: "Tên thư viện", kind: "text", min: 1, source: "BM09" },
  {
    key: "minReaderAge",
    label: "Tuổi độc giả tối thiểu",
    kind: "int",
    min: 1,
    max: 120,
    source: "QĐ01",
  },
  {
    key: "maxReaderAge",
    label: "Tuổi độc giả tối đa",
    kind: "int",
    min: 1,
    max: 120,
    source: "QĐ01",
  },
  {
    key: "cardValidityMonths",
    label: "Hạn thẻ (tháng)",
    kind: "int",
    min: 1,
    max: 120,
    source: "QĐ02",
  },
  {
    key: "publicationYearWindow",
    label: "Nhận sách xuất bản trong (năm)",
    kind: "int",
    min: 0,
    max: 200,
    source: "QĐ03",
  },
  {
    key: "maxBooksPerLoan",
    label: "Số cuốn tối đa mỗi phiếu",
    kind: "int",
    min: 1,
    max: 20,
    source: "QĐ05",
  },
  {
    key: "initialLoanDays",
    label: "Số ngày mượn tối đa",
    kind: "int",
    min: 1,
    max: 365,
    source: "QĐ06",
  },
  { key: "maxRenewals", label: "Số lần gia hạn", kind: "int", min: 0, max: 10, source: "QĐ06" },
  {
    key: "renewalDays",
    label: "Số ngày mỗi lần gia hạn",
    kind: "int",
    min: 1,
    max: 365,
    source: "QĐ06",
  },
  {
    key: "overdueFinePerDay",
    label: "Phí phạt trả trễ / ngày / cuốn",
    kind: "money",
    min: 0,
    source: "QĐ07",
  },
  {
    key: "allowedOutstandingBalance",
    label: "Ngưỡng chặn nợ phạt",
    kind: "money",
    min: 1,
    source: "QĐ12",
  },
  { key: "readyHoldDays", label: "Số ngày giữ chỗ", kind: "int", min: 1, max: 60, source: "BM09" },
  {
    key: "damageLostFees.MINOR_DAMAGE",
    label: "Phí hỏng nhẹ",
    kind: "money",
    min: 0,
    source: "BM09",
  },
  {
    key: "damageLostFees.MAJOR_DAMAGE",
    label: "Phí hỏng nặng",
    kind: "money",
    min: 0,
    source: "BM09",
  },
  {
    key: "damageLostFees.LOST",
    label: "Phí mất sách",
    kind: "money",
    min: LOST_FEE_MIN,
    max: LOST_FEE_MAX,
    source: "QĐ07",
  },
];

export type RuleDraft = Record<string, string>;

/** Scalar rule value as form text; "" when the rule is missing (v1 policies). */
export function ruleText(value: unknown): string {
  if (typeof value === "string" || typeof value === "number") return String(value);
  return value === undefined || value === null ? "" : JSON.stringify(value);
}

export function readRule(rules: Record<string, unknown>, key: string): unknown {
  return key
    .split(".")
    .reduce<unknown>(
      (value, part) =>
        value && typeof value === "object" ? (value as Record<string, unknown>)[part] : undefined,
      rules,
    );
}

/** Form values (strings) from stored rules; missing v1 keys fall back to defaults. */
export function toDraft(rules: Record<string, unknown> | undefined): RuleDraft {
  return Object.fromEntries(
    RULE_FIELDS.map(({ key }) => {
      const value = rules ? readRule(rules, key) : undefined;
      return [key, String(value ?? readRule(DEFAULT_RULES, key))];
    }),
  );
}

/** QĐ17: returns field errors; empty object means the draft is valid. */
export function validateDraft(draft: RuleDraft): Record<string, string> {
  const errors: Record<string, string> = {};
  for (const field of RULE_FIELDS) {
    const raw = (draft[field.key] ?? "").trim();
    if (field.kind === "text") {
      if (!raw) errors[field.key] = "Không được để trống.";
      else if (raw.length > 200) errors[field.key] = "Tối đa 200 ký tự.";
      continue;
    }
    if (!/^\d+$/.test(raw)) {
      errors[field.key] =
        field.kind === "money" ? "Nhập số tiền VND (số nguyên ≥ 0)." : "Nhập số nguyên.";
      continue;
    }
    const value = Number(raw);
    if (value < field.min) errors[field.key] = `Tối thiểu ${field.min.toLocaleString("vi-VN")}.`;
    else if (field.max !== undefined && value > field.max)
      errors[field.key] = `Tối đa ${field.max.toLocaleString("vi-VN")}.`;
  }
  if (!errors.minReaderAge && !errors.maxReaderAge) {
    if (Number(draft.minReaderAge) > Number(draft.maxReaderAge))
      errors.maxReaderAge = "Tuổi tối đa phải ≥ tuổi tối thiểu.";
  }
  return errors;
}

export function toRules(draft: RuleDraft): PolicyRules {
  const int = (key: string) => Number(draft[key]!.trim());
  const money = (key: string) => String(Number(draft[key]!.trim()));
  return {
    libraryName: draft.libraryName!.trim(),
    minReaderAge: int("minReaderAge"),
    maxReaderAge: int("maxReaderAge"),
    cardValidityMonths: int("cardValidityMonths"),
    maxBooksPerLoan: int("maxBooksPerLoan"),
    initialLoanDays: int("initialLoanDays"),
    maxRenewals: int("maxRenewals"),
    renewalDays: int("renewalDays"),
    overdueFinePerDay: money("overdueFinePerDay"),
    allowedOutstandingBalance: money("allowedOutstandingBalance"),
    publicationYearWindow: int("publicationYearWindow"),
    readyHoldDays: int("readyHoldDays"),
    damageLostAssessment: "MANUAL_APPROVAL",
    damageLostFees: {
      MINOR_DAMAGE: money("damageLostFees.MINOR_DAMAGE"),
      MAJOR_DAMAGE: money("damageLostFees.MAJOR_DAMAGE"),
      LOST: money("damageLostFees.LOST"),
    },
  };
}

type PolicyRow = {
  status: string;
  effective_from: string;
  effective_to?: string | null;
  rules: Record<string, unknown>;
};

/** The ACTIVE/SUPERSEDED version in force at `now`, as the API's active_policy(). */
export function policyInForce<T extends PolicyRow>(rows: T[], now: number): T | undefined {
  return rows.find(
    (row) =>
      (row.status === "ACTIVE" || row.status === "SUPERSEDED") &&
      new Date(row.effective_from).getTime() <= now &&
      (!row.effective_to || new Date(row.effective_to).getTime() > now),
  );
}
