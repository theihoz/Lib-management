import { useRef, useState } from "react";
import type { ReactNode } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useServices, useSession } from "../auth/session";
import { isStaff } from "../auth/session-state";
import { createIdempotencyKey } from "../api/idempotency";
import { ApiError } from "../api/errors";
import { formatDateTime } from "../lib/datetime";
import { formatVnd } from "../lib/money";
import { Badge, Button, Notice, Panel, Stats, Table } from "../ui/components";
import { ApiFailure, LoadingSkeleton } from "../features/live/common";
import { chargeReason, eligibilityReason, reservationStatus } from "../features/live/labels";

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

type Item = { key: string; title: string; meta: string; status: ReactNode; action: ReactNode };
function ItemList({ label, empty, items }: { label: string; empty: string; items: Item[] }) {
  if (!items.length) return <p className="empty-state">{empty}</p>;
  return (
    <ul className="item-list" aria-label={label}>
      {items.map((item) => (
        <li key={item.key}>
          <div className="item-main">
            <strong className="item-title">{item.title}</strong>
            <span className="muted">{item.meta}</span>
          </div>
          <div className="item-status">{item.status}</div>
          <div className="item-action">{item.action}</div>
        </li>
      ))}
    </ul>
  );
}

/** Counts shown above the tabs; reuses the open-loans query of the first tab. */
function Summary() {
  const services = useServices();
  const [now] = useState(() => Date.now());
  const loans = useQuery({
    queryKey: ["me", "loans", "OPEN"],
    queryFn: async ({ signal }) =>
      (
        await services.circulation.get_me_loans({
          params: { query: { status: "OPEN", limit: 100 } },
          signal,
        })
      ).data!.data,
  });
  if (!loans.data) return null;
  const due = loans.data.map((row) => new Date(row.loanItem.due_at).getTime());
  const overdue = due.filter((time) => time < now).length;
  const soon = due.filter((time) => time >= now && time - now <= 2 * DAY).length;
  return (
    <Stats
      items={[
        { label: "Đang mượn", value: String(loans.data.length) },
        { label: "Sắp đến hạn", value: String(soon), note: "Trong 2 ngày tới" },
        { label: "Quá hạn", value: String(overdue) },
      ]}
    />
  );
}

/** YC#9 / QĐ22: the reader's own loans, renewals, history and fines (FE08). */
function MyLibrary() {
  const services = useServices();
  const cache = useQueryClient();
  const key = useRef(createIdempotencyKey()).current;
  const [tab, setTab] = useState<"OPEN" | "ALL" | "HOLDS" | "FINES">("OPEN");
  const [now] = useState(() => Date.now());
  const [message, setMessage] = useState<{ tone: "info" | "danger"; text: string }>();
  const loans = useQuery({
    queryKey: ["me", "loans", tab],
    enabled: tab === "OPEN" || tab === "ALL",
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
  const holds = useQuery({
    queryKey: ["me", "reservations"],
    enabled: tab === "HOLDS",
    queryFn: async ({ signal }) =>
      (
        await services.circulation.get_me_reservations({
          params: { query: { limit: 100 } },
          signal,
        })
      ).data!.data.filter((row) => row.status === "QUEUED" || row.status === "READY"),
  });
  const cancel = useMutation({
    mutationFn: async (row: { id: string; version: number }) => {
      const body = { expectedVersion: row.version, reason: "Độc giả hủy trên portal" };
      return (
        await services.circulation.post_reservations_id_cancellations({
          params: {
            path: { id: row.id },
            header: { "Idempotency-Key": key.forPayload({ cancel: row.id, ...body }) },
          },
          body,
        })
      ).data!;
    },
    onSuccess: () => {
      key.reset();
      setMessage({ tone: "info", text: "Đã hủy đặt trước." });
      void cache.invalidateQueries({ queryKey: ["me", "reservations"] });
    },
    onError: (error) => setMessage({ tone: "danger", text: renewalError(error) }),
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
    ["HOLDS", "Đặt trước"],
    ["FINES", "Phạt của tôi"],
  ] as const;
  return (
    <Panel title="Thư viện của tôi" className="my-library">
      <div className="tabs" role="tablist" aria-label="Thư viện của tôi">
        {tabs.map(([value, label]) => (
          <button
            key={value}
            type="button"
            role="tab"
            aria-selected={tab === value}
            onClick={() => {
              setTab(value);
              setMessage(undefined);
            }}
          >
            {label}
          </button>
        ))}
      </div>
      {message && <Notice tone={message.tone}>{message.text}</Notice>}
      {tab === "HOLDS" ? (
        holds.isPending ? (
          <LoadingSkeleton />
        ) : holds.error ? (
          <ApiFailure error={holds.error} retry={() => void holds.refetch()} />
        ) : (
          <ItemList
            label="Đặt trước của tôi"
            empty="Bạn chưa đặt trước cuốn nào. Đặt trước từ trang sách khi sách đang được mượn hết."
            items={holds.data.map((row) => ({
              key: row.id,
              title: row.title ?? "Ấn bản đã đặt",
              meta: `Đặt ngày ${formatDateTime(row.created_at, true)}`,
              status:
                row.status === "READY" ? (
                  <Badge tone="success">
                    Sẵn sàng nhận
                    {row.ready_expires_at
                      ? ` đến ${formatDateTime(row.ready_expires_at, true)}`
                      : ""}
                  </Badge>
                ) : (
                  <Badge>{reservationStatus(row.status)}</Badge>
                ),
              action: (
                <Button
                  variant="secondary"
                  disabled={cancel.isPending}
                  aria-label={`Hủy đặt trước “${row.title ?? ""}”`}
                  onClick={() => cancel.mutate({ id: row.id, version: row.version })}
                >
                  Hủy đặt trước
                </Button>
              ),
            }))}
          />
        )
      ) : tab === "FINES" ? (
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
              formatDateTime(charge.created_at, true),
            ])}
            empty={{ title: "Không có khoản phạt", hint: "Bạn không nợ khoản phạt nào." }}
          />
        )
      ) : loans.isPending ? (
        <LoadingSkeleton />
      ) : loans.error ? (
        <ApiFailure error={loans.error} retry={() => void loans.refetch()} />
      ) : tab === "OPEN" ? (
        <ItemList
          label="Sách đang mượn"
          empty="Bạn không mượn cuốn nào. Tìm sách trong danh mục rồi mượn tại quầy thư viện."
          items={loans.data.map((row) => {
            const days = Math.ceil((new Date(row.loanItem.due_at).getTime() - now) / DAY);
            return {
              key: row.loanItem.id,
              title: row.title ?? row.copy.barcode,
              meta: `Phiếu ${row.loan.loan_no} · Gia hạn ${row.loan.renewal_count} lần`,
              status: (
                <span className="due">
                  <span>Hạn trả {formatDateTime(row.loanItem.due_at, true)}</span>
                  <Badge tone={days < 0 ? "danger" : days <= 2 ? "warning" : "success"}>
                    {days < 0
                      ? `Quá hạn ${-days} ngày`
                      : days === 0
                        ? "Đến hạn hôm nay"
                        : `Còn ${days} ngày`}
                  </Badge>
                </span>
              ),
              action: (
                <Button
                  variant="secondary"
                  disabled={renew.isPending}
                  aria-label={`Gia hạn phiếu ${row.loan.loan_no}`}
                  onClick={() => renew.mutate({ id: row.loan.id, version: row.loan.version })}
                >
                  Gia hạn
                </Button>
              ),
            };
          })}
        />
      ) : (
        <Table
          caption="Lịch sử mượn trả"
          headers={["Sách", "Ngày mượn", "Hạn trả", "Ngày trả"]}
          rows={loans.data.map((row) => [
            row.title ?? row.copy.barcode,
            formatDateTime(row.loanItem.issued_at, true),
            formatDateTime(row.loanItem.due_at, true),
            row.loanItem.closed_at ? formatDateTime(row.loanItem.closed_at, true) : "Đang mượn",
          ])}
          empty={{ title: "Chưa có lịch sử", hint: "Các lần mượn trả sẽ hiện tại đây." }}
        />
      )}
    </Panel>
  );
}

/** Account summary and, for linked readers, their loans, history, reservations and fines. */
export function MePage({ onLogout }: { onLogout: () => void }) {
  const session = useSession();
  const linked = !!session.account?.reader_id;
  const name = session.account?.display_name ?? "";
  return (
    <div className="me-layout">
      <div className="stack">
        {linked && (
          <>
            <p className="greeting">
              Xin chào, <strong>{name}</strong>
            </p>
            <Summary />
            <MyLibrary />
          </>
        )}
        {!linked && !isStaff(session.permissions) && (
          <Notice tone="warning">
            Tài khoản chưa gắn với hồ sơ độc giả nên chưa xem được sách đang mượn. Liên hệ quầy thư
            viện để được liên kết.
          </Notice>
        )}
      </div>
      <Panel title="Tài khoản" className="account-card">
        <div className="account-identity">
          <span className="avatar avatar-large" aria-hidden="true">
            {name.slice(0, 1).toLocaleUpperCase("vi")}
          </span>
          <div>
            <strong>{name || "—"}</strong>
            <Badge tone={session.account?.status === "ACTIVE" ? "success" : "warning"}>
              {session.account?.status === "ACTIVE" ? "Đang hoạt động" : "Tạm khóa"}
            </Badge>
          </div>
        </div>
        <dl className="detail-list">
          <div>
            <dt>Hồ sơ độc giả</dt>
            <dd>
              {linked
                ? "Đã liên kết"
                : isStaff(session.permissions)
                  ? "Tài khoản nhân viên"
                  : "Chưa liên kết"}
            </dd>
          </div>
        </dl>
        <Button variant="secondary" icon="logout" onClick={onLogout}>
          Đăng xuất
        </Button>
      </Panel>
    </div>
  );
}
