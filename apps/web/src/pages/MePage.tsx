import { useRef, useState } from "react";
import { Link } from "react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useServices, useSession } from "../auth/session";
import { canOpen, isStaff } from "../auth/session-state";
import { createIdempotencyKey } from "../api/idempotency";
import { ApiError } from "../api/errors";
import { screens } from "../app/screens";
import { formatDateTime } from "../lib/datetime";
import { formatVnd } from "../lib/money";
import { Badge, Button, Notice, Panel, Table } from "../ui/components";
import { ApiFailure, LoadingSkeleton } from "../features/live/common";
import { chargeReason, eligibilityReason } from "../features/live/labels";

const DAY = 86_400_000;

/** Why the server refused a renewal, in the reader's words. */
function renewalError(error: unknown): string {
  if (!(error instanceof ApiError)) return "Không gia hạn được. Vui lòng thử lại.";
  const reasons = error.details
    .flatMap((detail) =>
      detail && typeof detail === "object" && "reasons" in detail && Array.isArray(detail.reasons)
        ? (detail.reasons as string[])
        : [],
    )
    .map(eligibilityReason);
  return reasons.length ? reasons.join("; ") : error.message;
}

/** YC#9 / QĐ22: the reader's own loans, renewals, history and fines (FE08). */
function MyLibrary() {
  const services = useServices();
  const cache = useQueryClient();
  const key = useRef(createIdempotencyKey()).current;
  const [tab, setTab] = useState<"OPEN" | "ALL" | "FINES">("OPEN");
  const [now] = useState(() => Date.now());
  const [message, setMessage] = useState<{ tone: "info" | "danger"; text: string }>();
  const loans = useQuery({
    queryKey: ["me", "loans", tab],
    enabled: tab !== "FINES",
    queryFn: async ({ signal }) =>
      (
        await services.circulation.get_me_loans({
          params: { query: { status: tab === "ALL" ? "ALL" : "OPEN", limit: 100 } },
          signal,
        })
      ).data!.data,
  });
  const fines = useQuery({
    queryKey: ["me", "fines"],
    enabled: tab === "FINES",
    queryFn: async ({ signal }) =>
      (await services.finance.get_me_fine_charges({ params: { query: { limit: 100 } }, signal }))
        .data!.data,
  });
  const renew = useMutation({
    mutationFn: async (loan: { id: string; version: number }) => {
      const body = { expectedVersion: loan.version };
      return (
        await services.circulation.post_loans_id_renewals({
          params: {
            path: { id: loan.id },
            header: { "Idempotency-Key": key.forPayload({ id: loan.id, ...body }) },
          },
          body,
        })
      ).data!;
    },
    onSuccess: () => {
      key.reset();
      setMessage({ tone: "info", text: "Đã gia hạn. Hạn trả mới hiển thị trong danh sách." });
      void cache.invalidateQueries({ queryKey: ["me", "loans"] });
    },
    onError: (error) => setMessage({ tone: "danger", text: renewalError(error) }),
  });
  const tabs = [
    ["OPEN", "Đang mượn"],
    ["ALL", "Lịch sử"],
    ["FINES", "Phạt của tôi"],
  ] as const;
  return (
    <Panel title="Thư viện của tôi">
      <div className="actions" role="tablist" aria-label="Thư viện của tôi">
        {tabs.map(([value, label]) => (
          <Button
            key={value}
            role="tab"
            aria-selected={tab === value}
            variant={tab === value ? "primary" : "secondary"}
            onClick={() => {
              setTab(value);
              setMessage(undefined);
            }}
          >
            {label}
          </Button>
        ))}
      </div>
      {message && <Notice tone={message.tone}>{message.text}</Notice>}
      {tab === "FINES" ? (
        fines.isPending ? (
          <LoadingSkeleton />
        ) : fines.error ? (
          <ApiFailure error={fines.error} retry={() => void fines.refetch()} />
        ) : (
          <Table
            caption="Khoản phạt của tôi"
            headers={["Lý do", "Số tiền", "Còn nợ", "Ngày ghi nhận"]}
            rows={fines.data.map((charge) => [
              chargeReason(charge.reason),
              formatVnd(charge.assessed_amount),
              formatVnd(charge.balance ?? "0"),
              formatDateTime(charge.created_at),
            ])}
            empty={{ title: "Không có khoản phạt", hint: "Bạn không nợ khoản phạt nào." }}
          />
        )
      ) : loans.isPending ? (
        <LoadingSkeleton />
      ) : loans.error ? (
        <ApiFailure error={loans.error} retry={() => void loans.refetch()} />
      ) : (
        <Table
          caption={tab === "OPEN" ? "Sách đang mượn" : "Lịch sử mượn trả"}
          headers={
            tab === "OPEN"
              ? ["Sách", "Phiếu", "Hạn trả", "Đã gia hạn"]
              : ["Sách", "Ngày mượn", "Hạn trả", "Ngày trả"]
          }
          rows={loans.data.map((row) => {
            const late = now > new Date(row.loanItem.due_at).getTime();
            return tab === "OPEN"
              ? [
                  row.title ?? row.copy.barcode,
                  row.loan.loan_no,
                  `${formatDateTime(row.loanItem.due_at)}${late ? ` (quá hạn ${Math.floor((now - new Date(row.loanItem.due_at).getTime()) / DAY)} ngày)` : ""}`,
                  `${row.loan.renewal_count} lần`,
                ]
              : [
                  row.title ?? row.copy.barcode,
                  formatDateTime(row.loanItem.issued_at),
                  formatDateTime(row.loanItem.due_at),
                  row.loanItem.closed_at ? formatDateTime(row.loanItem.closed_at) : "Đang mượn",
                ];
          })}
          empty={{
            title: tab === "OPEN" ? "Không có sách đang mượn" : "Chưa có lịch sử",
            hint: "Mượn sách tại quầy thư viện.",
          }}
        />
      )}
      {tab === "OPEN" && loans.data && loans.data.length > 0 && (
        <div className="actions">
          {[...new Map(loans.data.map((row) => [row.loan.id, row])).values()].map((row) => (
            <Button
              key={row.loan.id}
              variant="secondary"
              disabled={renew.isPending}
              onClick={() => renew.mutate({ id: row.loan.id, version: row.loan.version })}
            >
              Gia hạn phiếu {row.loan.loan_no}
            </Button>
          ))}
        </div>
      )}
    </Panel>
  );
}

const PERMISSION_GROUPS: [string, string][] = [
  ["catalog.", "Danh mục"],
  ["reader.", "Độc giả"],
  ["card.", "Thẻ"],
  ["loan.", "Mượn / gia hạn"],
  ["return.", "Trả sách"],
  ["assessment.", "Đánh giá phí"],
  ["payment.", "Thu tiền"],
  ["charge.", "Phí"],
  ["finance.", "Tài chính"],
  ["ledger.", "Sổ cái"],
  ["overdue.", "Quá hạn"],
  ["report.", "Báo cáo"],
  ["export.", "Xuất dữ liệu"],
  ["policy.", "Quy định"],
];

/** Account summary, shortcuts the account may use, and its permissions grouped by area. */
export function MePage({ onLogout }: { onLogout: () => void }) {
  const session = useSession();
  const shortcuts = screens.filter(
    (item) =>
      !item.path.includes(":") &&
      item.permission &&
      item.permission !== "session" &&
      canOpen(session.status, session.permissions, item),
  );
  const grouped = PERMISSION_GROUPS.map(([prefix, label]) => ({
    label,
    codes: session.permissions.filter((code) => code.startsWith(prefix)),
  })).filter((group) => group.codes.length);
  return (
    <div className="stack">
      <Panel title="Tài khoản">
        <dl className="detail-list">
          <div>
            <dt>Tên hiển thị</dt>
            <dd>{session.account?.display_name ?? "—"}</dd>
          </div>
          <div>
            <dt>Trạng thái</dt>
            <dd>
              <Badge tone={session.account?.status === "ACTIVE" ? "success" : "warning"}>
                {session.account?.status === "ACTIVE" ? "Đang hoạt động" : session.account?.status}
              </Badge>
            </dd>
          </div>
          <div>
            <dt>Hồ sơ độc giả</dt>
            <dd>
              {session.account?.reader_id
                ? "Đã liên kết"
                : isStaff(session.permissions)
                  ? "Không áp dụng (tài khoản nhân viên)"
                  : "Chưa liên kết — liên hệ thủ thư"}
            </dd>
          </div>
        </dl>
        <div className="actions">
          <Button variant="secondary" icon="logout" onClick={onLogout}>
            Đăng xuất
          </Button>
        </div>
      </Panel>
      {session.account?.reader_id && <MyLibrary />}
      <Panel
        title="Lối tắt công việc"
        subtitle="Chỉ hiển thị chức năng tài khoản này được phép dùng."
      >
        {shortcuts.length ? (
          <ul className="shortcut-list">
            {shortcuts.map((item) => (
              <li key={item.id}>
                <Link to={item.path}>{item.title}</Link>
              </li>
            ))}
          </ul>
        ) : (
          <p className="muted">
            Tài khoản này chưa có chức năng nghiệp vụ. Bạn có thể{" "}
            <Link to="/catalog">tìm sách trong danh mục</Link>.
          </p>
        )}
      </Panel>
      <Panel title="Quyền hiện tại" subtitle="Do máy chủ xác định; giao diện chỉ phản ánh.">
        {grouped.length ? (
          <dl className="detail-list">
            {grouped.map((group) => (
              <div key={group.label}>
                <dt>{group.label}</dt>
                <dd>{group.codes.join(", ")}</dd>
              </div>
            ))}
          </dl>
        ) : (
          <p className="muted">Không có quyền nghiệp vụ ngoài tra cứu danh mục.</p>
        )}
      </Panel>
    </div>
  );
}
