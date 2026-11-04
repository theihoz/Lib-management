import { useRef, useState, type ReactNode } from "react";
import { Link, useNavigate, useParams } from "react-router";
import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useServices, useSession } from "../../auth/session";
import { createIdempotencyKey } from "../../api/idempotency";
import type { components } from "../../api/schema";
import { useDebounced } from "../../lib/useDebounced";
import { formatDateTime } from "../../lib/datetime";
import { Badge, Button, Dialog, Field, Panel, Table } from "../../ui/components";
import type { ScreenDefinition } from "../types";
import { ApiFailure, LoadingSkeleton, MutationFeedback } from "./common";
import { cardStatus, chargeReason, eligibilityReason } from "./labels";
import { formatVnd } from "../../lib/money";

function ReaderList() {
  const services = useServices();
  const session = useSession();
  const navigate = useNavigate();
  const [search, setSearch] = useState("");
  const query = useDebounced(search);
  const result = useInfiniteQuery({
    queryKey: ["readers", query],
    initialPageParam: undefined as string | undefined,
    queryFn: async ({ pageParam, signal }) =>
      (
        await services.readers.get_readers({
          params: { query: { query, cursor: pageParam, limit: 20 } },
          signal,
        })
      ).data!,
    getNextPageParam: (page) => page.nextCursor ?? undefined,
  });
  const readers = result.data?.pages.flatMap((page) => page.data) ?? [];
  return (
    <div className="stack">
      <div className="toolbar">
        <Field
          label="Tìm độc giả"
          type="search"
          placeholder="Họ tên, mã độc giả hoặc email…"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
        />
        {session.permissions.includes("reader.write") && (
          <Link className="button button-primary" to="/staff/readers/new">
            Thêm độc giả
          </Link>
        )}
      </div>
      {result.isPending ? (
        <LoadingSkeleton />
      ) : result.error ? (
        <ApiFailure
          error={result.error}
          retry={() => {
            void result.refetch();
          }}
        />
      ) : (
        <Panel>
          <Table
            headers={["Mã độc giả", "Họ tên", "Email", "Loại", "Trạng thái"]}
            rows={readers.map((reader) => [
              reader.reader_code,
              reader.full_name,
              reader.email ?? "—",
              reader.reader_type,
              reader.status,
            ])}
            onRow={(index) => {
              void navigate(`/staff/readers/${readers[index]!.id}`);
            }}
            caption="Độc giả thư viện"
          />
        </Panel>
      )}
      {result.hasNextPage && (
        <Button
          variant="secondary"
          disabled={result.isFetchingNextPage}
          onClick={() => {
            void result.fetchNextPage();
          }}
        >
          Tải thêm 20 độc giả
        </Button>
      )}
    </div>
  );
}
function ReaderForm() {
  const services = useServices();
  const cache = useQueryClient();
  const key = useRef(createIdempotencyKey()).current;
  const [body, setBody] = useState<components["schemas"]["ReaderCreate"]>({
    readerCode: "",
    fullName: "",
    birthDate: "",
    readerType: "X",
    email: "",
    phone: "",
    address: "",
  });
  const save = useMutation({
    mutationFn: async () =>
      (
        await services.readers.post_readers({
          body: {
            ...body,
            email: body.email || null,
            phone: body.phone || null,
            address: body.address || null,
          },
          params: { header: { "Idempotency-Key": key.forPayload(body) } },
        })
      ).data!,
    onSuccess: () => {
      key.reset();
      void cache.invalidateQueries({ queryKey: ["readers"] });
    },
  });
  return (
    <Panel title="Hồ sơ độc giả">
      <form
        onSubmit={(event) => {
          event.preventDefault();
          save.mutate();
        }}
      >
        <div className="form-grid">
          <Field
            label="Mã độc giả"
            required
            maxLength={32}
            value={body.readerCode}
            onChange={(event) => setBody({ ...body, readerCode: event.target.value })}
          />
          <Field
            label="Họ tên"
            required
            maxLength={200}
            value={body.fullName}
            onChange={(event) => setBody({ ...body, fullName: event.target.value })}
          />
          <Field
            label="Ngày sinh"
            required
            type="date"
            value={body.birthDate}
            max={new Date().toISOString().slice(0, 10)}
            hint="Độc giả từ 12 đến 55 tuổi (QĐ01)."
            onChange={(event) => setBody({ ...body, birthDate: event.target.value })}
          />
          <div className="field">
            <label htmlFor="reader-type">Loại độc giả</label>
            <select
              id="reader-type"
              value={body.readerType}
              onChange={(event) =>
                setBody({
                  ...body,
                  readerType: event.target
                    .value as components["schemas"]["ReaderCreate"]["readerType"],
                })
              }
            >
              <option value="X">X</option>
              <option value="Y">Y</option>
              <option value="Z">Z</option>
            </select>
          </div>
          <Field
            label="Email"
            type="email"
            value={body.email ?? ""}
            onChange={(event) => setBody({ ...body, email: event.target.value })}
          />
          <Field
            label="Điện thoại"
            type="tel"
            value={body.phone ?? ""}
            onChange={(event) => setBody({ ...body, phone: event.target.value })}
          />
          <Field
            label="Địa chỉ"
            value={body.address ?? ""}
            onChange={(event) => setBody({ ...body, address: event.target.value })}
          />
        </div>
        <MutationFeedback error={save.error} success={save.isSuccess}>
          {save.data && (
            <Link to={`/staff/readers/${save.data.id}`}>Đã tạo hồ sơ. Mở chi tiết độc giả.</Link>
          )}
        </MutationFeedback>
        <div className="actions">
          <Button type="submit" disabled={save.isPending} aria-busy={save.isPending}>
            {save.isPending ? "Đang lưu…" : "Lưu hồ sơ"}
          </Button>
          <Link className="button button-secondary" to="/staff/readers">
            Về danh sách
          </Link>
        </div>
      </form>
    </Panel>
  );
}
function ReaderProfile() {
  const { readerId = "" } = useParams();
  const services = useServices();
  const session = useSession();
  const reader = useQuery({
    queryKey: ["reader", readerId],
    queryFn: async ({ signal }) =>
      (await services.readers.get_readers_id({ params: { path: { id: readerId } }, signal })).data!,
  });
  const eligibility = useQuery({
    queryKey: ["reader", readerId, "eligibility"],
    queryFn: async ({ signal }) =>
      (
        await services.readers.get_readers_id_eligibility({
          params: { path: { id: readerId } },
          signal,
        })
      ).data!,
    enabled: session.permissions.includes("eligibility.read"),
    staleTime: 0,
  });
  if (reader.isPending) return <LoadingSkeleton />;
  if (reader.error) return <ApiFailure error={reader.error} />;
  return (
    <div className="stack">
      <Panel title={reader.data.full_name} subtitle={reader.data.reader_code}>
        <Badge tone={reader.data.status === "ACTIVE" ? "success" : "warning"}>
          {reader.data.status}
        </Badge>
        <dl className="detail-list">
          {[
            ["Email", reader.data.email],
            ["Điện thoại", reader.data.phone],
            ["Ngày sinh", reader.data.birth_date],
            ["Loại độc giả", reader.data.reader_type],
            ["Địa chỉ", reader.data.address],
          ].map(([label, value]) => (
            <div key={label}>
              <dt>{label}</dt>
              <dd>{value ?? "—"}</dd>
            </div>
          ))}
        </dl>
        <div className="live-data-links">
          {session.permissions.includes("card.issue") && (
            <Link
              className="button button-secondary"
              to={`/staff/readers/cards/new?reader=${readerId}`}
            >
              Cấp thẻ thư viện
            </Link>
          )}
          {session.permissions.includes("loan.checkout") && (
            <Link className="button button-primary" to={`/staff/checkout?reader=${readerId}`}>
              Lập phiếu mượn
            </Link>
          )}
        </div>
      </Panel>
      {eligibility.data && (
        <Panel title="Điều kiện mượn">
          <Badge tone={eligibility.data.allowed ? "success" : "warning"}>
            {eligibility.data.allowed ? "Đủ điều kiện" : "Chưa đủ điều kiện"}
          </Badge>
          <ul>
            {eligibility.data.reasons.map((reason) => (
              <li key={reason}>{eligibilityReason(reason)}</li>
            ))}
          </ul>
        </Panel>
      )}
      {eligibility.error && (
        <ApiFailure
          error={eligibility.error}
          retry={() => {
            void eligibility.refetch();
          }}
        />
      )}
      <ReaderCards readerId={readerId} canChange={session.permissions.includes("card.issue")} />
      <ReaderActivity readerId={readerId} permissions={session.permissions} />
    </div>
  );
}

const DAY = 86_400_000;
const CLOSURE: Record<string, string> = { RETURNED: "Đã trả", LOST: "Báo mất", VOIDED: "Hủy" };
const RESERVATION: Record<string, string> = { QUEUED: "Đang chờ", READY: "Sẵn sàng nhận" };

/** YC#17 / BM12 / QĐ22: what the reader has now and has had. */
function ReaderActivity({
  readerId,
  permissions,
}: {
  readerId: string;
  permissions: readonly string[];
}) {
  const services = useServices();
  const [now] = useState(() => Date.now());
  const [cursor, setCursor] = useState<string>();
  const loans = useQuery({
    queryKey: ["reader", readerId, "loans"],
    queryFn: async ({ signal }) =>
      (
        await services.circulation.get_loans({
          params: { query: { readerId, status: "OPEN", limit: 100 } },
          signal,
        })
      ).data!.data,
  });
  const fines = useQuery({
    queryKey: ["reader", readerId, "fines"],
    enabled: permissions.includes("finance.read"),
    queryFn: async ({ signal }) =>
      (
        await services.finance.get_fine_charges({
          params: { query: { readerId, limit: 100 } },
          signal,
        })
      ).data!.data.filter((charge) => charge.balance !== "0"),
  });
  const holds = useQuery({
    queryKey: ["reader", readerId, "reservations"],
    enabled: permissions.includes("reservation.read"),
    queryFn: async ({ signal }) =>
      (
        await services.circulation.get_reservations({
          params: { query: { readerId, status: "ACTIVE", limit: 100 } },
          signal,
        })
      ).data!.data,
  });
  const history = useQuery({
    queryKey: ["reader", readerId, "history", cursor],
    queryFn: async ({ signal }) =>
      (
        await services.circulation.get_readers_id_history({
          params: { path: { id: readerId }, query: { cursor, limit: 20 } },
          signal,
        })
      ).data!,
    placeholderData: (previous) => previous,
  });
  const owed = (fines.data ?? []).reduce((sum, charge) => sum + BigInt(charge.balance ?? "0"), 0n);
  const section = <T,>(
    query: { isPending: boolean; error: unknown; refetch: () => unknown; data?: T },
    render: (data: T) => ReactNode,
  ) =>
    query.isPending ? (
      <LoadingSkeleton />
    ) : query.error ? (
      <ApiFailure error={query.error} retry={() => void query.refetch()} />
    ) : (
      render(query.data as T)
    );
  return (
    <>
      <Panel title="Đang mượn">
        {section(loans, (rows) => (
          <Table
            caption="Sách đang mượn"
            headers={["Phiếu", "Sách", "Mã vạch", "Hạn trả", "Quá hạn"]}
            rows={rows.map((row) => {
              const late = Math.floor((now - new Date(row.loanItem.due_at).getTime()) / DAY);
              return [
                row.loan.loan_no,
                row.title ?? "—",
                row.copy.barcode,
                formatDateTime(row.loanItem.due_at),
                late > 0 ? `${late} ngày` : "—",
              ];
            })}
            empty={{ title: "Không có sách đang mượn", hint: "Độc giả đã trả hết sách." }}
          />
        ))}
      </Panel>
      {permissions.includes("finance.read") && (
        <Panel title="Phạt chưa thu">
          {section(fines, (rows) => (
            <>
              <Table
                caption="Khoản phạt còn nợ"
                headers={["Lý do", "Số tiền", "Còn nợ", "Ngày ghi nhận"]}
                rows={rows.map((charge) => [
                  chargeReason(charge.reason),
                  formatVnd(charge.assessed_amount),
                  formatVnd(charge.balance ?? "0"),
                  formatDateTime(charge.created_at),
                ])}
                empty={{ title: "Không nợ phạt", hint: "Độc giả không còn khoản phạt nào." }}
              />
              <p>
                Tổng còn nợ: <strong>{formatVnd(owed.toString())}</strong>
              </p>
            </>
          ))}
        </Panel>
      )}
      {permissions.includes("reservation.read") && (
        <Panel title="Đặt trước đang chờ">
          {section(holds, (rows) => (
            <Table
              caption="Đặt trước đang chờ"
              headers={["Ấn bản", "Trạng thái", "Ngày đặt", "Hạn nhận"]}
              rows={rows.map((row) => [
                row.edition_id,
                RESERVATION[row.status] ?? row.status,
                formatDateTime(row.created_at),
                row.ready_expires_at ? formatDateTime(row.ready_expires_at) : "—",
              ])}
              empty={{ title: "Không có đặt trước", hint: "Độc giả chưa đặt trước sách nào." }}
            />
          ))}
        </Panel>
      )}
      <Panel title="Lịch sử mượn trả">
        {section(history, (page) => (
          <>
            <Table
              caption="Lịch sử mượn trả"
              headers={["Ngày mượn", "Hạn trả", "Ngày trả", "Kết quả"]}
              rows={page.data.map((item) => [
                formatDateTime(item.issued_at),
                formatDateTime(item.due_at),
                item.closed_at ? formatDateTime(item.closed_at) : "Đang mượn",
                item.closure_reason ? (CLOSURE[item.closure_reason] ?? item.closure_reason) : "—",
              ])}
            />
            <div className="actions">
              {cursor && (
                <Button variant="secondary" onClick={() => setCursor(undefined)}>
                  Về trang đầu
                </Button>
              )}
              {page.nextCursor && (
                <Button variant="secondary" onClick={() => setCursor(page.nextCursor ?? undefined)}>
                  Trang sau
                </Button>
              )}
            </div>
          </>
        ))}
      </Panel>
    </>
  );
}
type ReaderCardRow = components["schemas"]["ReaderCard"];
function ReaderCards({ readerId, canChange }: { readerId: string; canChange: boolean }) {
  const services = useServices();
  const cache = useQueryClient();
  const key = useRef(createIdempotencyKey()).current;
  const [target, setTarget] = useState<ReaderCardRow>();
  const [reason, setReason] = useState("");
  const [now] = useState(() => Date.now());
  const cards = useQuery({
    queryKey: ["reader", readerId, "cards"],
    queryFn: async ({ signal }) =>
      (await services.readers.get_readers_id_cards({ params: { path: { id: readerId } }, signal }))
        .data!,
  });
  const blocking = target?.status === "ACTIVE";
  const change = useMutation({
    mutationFn: async () => {
      const body = {
        expectedVersion: target!.version,
        status: blocking ? ("BLOCKED" as const) : ("ACTIVE" as const),
        reason: reason.trim() || null,
      };
      return (
        await services.readers.patch_reader_cards_id({
          params: {
            path: { id: target!.id },
            header: { "Idempotency-Key": key.forPayload({ id: target!.id, ...body }) },
          },
          body,
        })
      ).data!;
    },
    onSuccess: () => {
      key.reset();
      setTarget(undefined);
      void cache.invalidateQueries({ queryKey: ["reader", readerId] });
    },
  });
  const changeable = (card: ReaderCardRow) =>
    canChange &&
    (card.status === "ACTIVE" || card.status === "BLOCKED") &&
    new Date(card.expires_at).getTime() > now;
  return (
    <Panel title="Thẻ thư viện">
      {cards.isPending ? (
        <LoadingSkeleton />
      ) : cards.error ? (
        <ApiFailure error={cards.error} retry={() => void cards.refetch()} />
      ) : (
        <>
          <Table
            caption="Thẻ thư viện của độc giả"
            headers={["Số thẻ", "Trạng thái", "Ngày cấp", "Hết hạn"]}
            rows={cards.data.map((card) => [
              card.card_no,
              cardStatus(card, now),
              formatDateTime(card.issued_at),
              formatDateTime(card.expires_at),
            ])}
            onRow={(index) => {
              const picked = cards.data[index];
              if (picked && changeable(picked)) {
                setTarget(picked);
                setReason("");
                change.reset();
              }
            }}
          />
          {canChange && (
            <p className="muted">Bấm số thẻ đang hoạt động hoặc tạm khóa để khóa/mở khóa.</p>
          )}
          <MutationFeedback success={change.isSuccess}>
            Đã cập nhật trạng thái thẻ.
          </MutationFeedback>
        </>
      )}
      <Dialog
        open={!!target}
        title={blocking ? "Tạm khóa thẻ" : "Mở khóa thẻ"}
        pending={change.isPending}
        onClose={() => setTarget(undefined)}
      >
        <form
          onSubmit={(event) => {
            event.preventDefault();
            change.mutate();
          }}
        >
          <p>
            Thẻ <strong>{target?.card_no}</strong>:{" "}
            {blocking
              ? "độc giả sẽ không mượn được cho đến khi mở khóa."
              : "thẻ hoạt động lại đến hết hạn."}
          </p>
          <Field
            label="Lý do"
            required={blocking}
            maxLength={500}
            value={reason}
            onChange={(event) => setReason(event.target.value)}
          />
          <MutationFeedback error={change.error} />
          <div className="actions">
            <Button type="submit" disabled={change.isPending}>
              {blocking ? "Khóa thẻ" : "Mở khóa"}
            </Button>
            <Button variant="secondary" onClick={() => setTarget(undefined)}>
              Hủy
            </Button>
          </div>
        </form>
      </Dialog>
    </Panel>
  );
}
function IssueCard() {
  const services = useServices();
  const cache = useQueryClient();
  const key = useRef(createIdempotencyKey()).current;
  const [reader, setReader] = useState(
    new URLSearchParams(window.location.search).get("reader") ?? "",
  );
  const save = useMutation({
    mutationFn: async () =>
      (
        await services.readers.post_readers_id_cards({
          params: {
            path: { id: reader },
            header: { "Idempotency-Key": key.forPayload({ reader }) },
          },
        })
      ).data!,
    onSuccess: () => {
      key.reset();
      void cache.invalidateQueries({ queryKey: ["reader", reader] });
    },
  });
  return (
    <Panel title="Cấp thẻ thư viện">
      <form
        onSubmit={(event) => {
          event.preventDefault();
          save.mutate();
        }}
      >
        <Field
          label="Mã định danh độc giả"
          value={reader}
          onChange={(event) => setReader(event.target.value)}
          required
          placeholder="Chọn từ hồ sơ độc giả"
        />
        <p className="data-description">
          Ngày hết hạn do hệ thống xác định theo quy định đang áp dụng.
        </p>
        <MutationFeedback error={save.error} success={save.isSuccess}>
          {save.data && `Đã cấp thẻ ${save.data.card_no}. Hạn thẻ: ${save.data.expires_at}.`}
        </MutationFeedback>
        <div className="actions">
          <Button type="submit" disabled={save.isPending}>
            Xác nhận cấp thẻ
          </Button>
        </div>
      </form>
    </Panel>
  );
}
export default function Readers({ screen }: { screen: ScreenDefinition }) {
  if (screen.id === "FE03.01") return <ReaderList />;
  if (screen.id === "FE03.02") return <ReaderProfile />;
  if (screen.id === "FE03.04") return <IssueCard />;
  return <ReaderForm />;
}
