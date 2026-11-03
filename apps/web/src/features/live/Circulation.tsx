import { useRef, useState } from "react";
import type { ReactNode } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams } from "react-router";
import { useServices, useSession } from "../../auth/session";
import { createIdempotencyKey } from "../../api/idempotency";
import type { components } from "../../api/schema";
import {
  Badge,
  Button,
  Dialog,
  Field,
  Notice,
  Panel,
  ProgressSteps,
  Table,
} from "../../ui/components";
import { formatDateTime } from "../../lib/datetime";
import type { ScreenDefinition } from "../types";
import { ApiFailure, LoadingSkeleton, MutationFeedback } from "./common";
import { ReaderPicker } from "./ReaderPicker";
import type { Reader } from "./ReaderPicker";

type LoanRow = components["schemas"]["LoanLookupRow"];
type Scanned = { copyId: string; barcode: string; title: string };

const MAX_COPIES = 4;

function message(error: unknown): string {
  return error instanceof Error ? error.message : "Không thể thực hiện. Vui lòng thử lại.";
}

function Checkout() {
  const services = useServices();
  const cache = useQueryClient();
  const key = useRef(createIdempotencyKey()).current;
  const [reader, setReader] = useState<Reader>();
  const [barcode, setBarcode] = useState("");
  const [scanned, setScanned] = useState<Scanned[]>([]);
  const [scanError, setScanError] = useState("");
  const [confirm, setConfirm] = useState(false);

  const eligibility = useQuery({
    queryKey: ["reader", reader?.id, "eligibility"],
    queryFn: async ({ signal }) =>
      (
        await services.readers.get_readers_id_eligibility({
          params: { path: { id: reader!.id } },
          signal,
        })
      ).data!,
    enabled: !!reader,
    staleTime: 0,
    retry: false,
  });
  const scan = useMutation({
    mutationFn: async (code: string) =>
      (await services.catalog.get_copies_lookup({ params: { query: { barcode: code } } })).data!,
    onSuccess: (found) => {
      if (scanned.some((item) => item.copyId === found.copy.id))
        return setScanError("Bản sách này đã được chọn.");
      if (scanned.length >= MAX_COPIES)
        return setScanError(`Mỗi phiếu tối đa ${MAX_COPIES} bản sách.`);
      if (found.loanItem) return setScanError("Bản sách đang được mượn.");
      if (found.copy.status !== "AVAILABLE")
        return setScanError(`Bản sách không sẵn sàng cho mượn (${found.copy.status}).`);
      setScanned([
        ...scanned,
        { copyId: found.copy.id, barcode: found.copy.barcode, title: found.edition.title },
      ]);
      setBarcode("");
      setScanError("");
    },
    onError: (error) => setScanError(message(error)),
  });
  const checkout = useMutation({
    mutationFn: async () => {
      const body = { readerId: reader!.id, copyIds: scanned.map((item) => item.copyId) };
      return (
        await services.circulation.post_loans({
          body,
          params: { header: { "Idempotency-Key": key.forPayload(body) } },
        })
      ).data!;
    },
    onSuccess: () => {
      key.reset();
      setConfirm(false);
      void cache.invalidateQueries({ queryKey: ["reader"] });
      void cache.invalidateQueries({ queryKey: ["catalog"] });
      void cache.invalidateQueries({ queryKey: ["loans"] });
    },
    // Keep the dialog open state and the scanned list so the operator can retry.
    onError: () => setConfirm(false),
  });
  const done = checkout.isSuccess;
  const step = done ? 3 : confirm ? 2 : reader ? 1 : 0;
  const reset = () => {
    key.reset();
    checkout.reset();
    setReader(undefined);
    setScanned([]);
    setBarcode("");
    setScanError("");
  };
  return (
    <div className="stack">
      <ProgressSteps current={step} />
      <div className="counter-layout">
        <div className="stack">
          <Panel title="Xác định độc giả">
            {reader ? (
              <div className="reader-strip" aria-live="polite">
                <strong>{reader.full_name}</strong> · {reader.reader_code}
                {!done && (
                  <Button
                    variant="ghost"
                    onClick={() => {
                      setReader(undefined);
                      setScanned([]);
                    }}
                  >
                    Đổi độc giả
                  </Button>
                )}
              </div>
            ) : (
              <ReaderPicker onPick={setReader} />
            )}
            {eligibility.error && <ApiFailure error={eligibility.error} />}
          </Panel>
          {reader && !done && (
            <Panel title="Quét sách">
              <form
                className="scan-form"
                onSubmit={(event) => {
                  event.preventDefault();
                  const code = barcode.trim();
                  if (code) scan.mutate(code);
                }}
              >
                <Field
                  label="Mã vạch bản sách"
                  required
                  value={barcode}
                  onChange={(event) => setBarcode(event.target.value)}
                  error={scanError || undefined}
                />
                <Button type="submit" variant="secondary" aria-busy={scan.isPending}>
                  Thêm sách
                </Button>
              </form>
              <ul className="selected-copies">
                {scanned.map((item) => (
                  <li key={item.copyId}>
                    <span>
                      {item.title} <code>{item.barcode}</code>
                    </span>
                    <Button
                      variant="ghost"
                      onClick={() =>
                        setScanned(scanned.filter((other) => other.copyId !== item.copyId))
                      }
                    >
                      Bỏ chọn
                    </Button>
                  </li>
                ))}
              </ul>
            </Panel>
          )}
        </div>
        <Panel title="Điều kiện mượn">
          {reader ? (
            <>
              <div aria-live="polite">
                <Badge tone={eligibility.data?.allowed ? "success" : "warning"}>
                  {eligibility.isFetching
                    ? "Đang kiểm tra…"
                    : eligibility.data?.allowed
                      ? "Đủ điều kiện"
                      : "Chưa đủ điều kiện"}
                </Badge>
                <ul>
                  {eligibility.data?.reasons.map((reason) => (
                    <li key={reason}>{reason}</li>
                  ))}
                </ul>
              </div>
              <p className="muted">
                Đã chọn {scanned.length} / {MAX_COPIES} cuốn.
              </p>
              <div className="actions">
                <Button
                  disabled={
                    done || !eligibility.data?.allowed || !scanned.length || checkout.isPending
                  }
                  onClick={() => setConfirm(true)}
                >
                  Xác nhận mượn sách
                </Button>
              </div>
              <p className="data-description">
                Hạn trả và điều kiện được hệ thống kiểm tra lại khi xác nhận.
              </p>
            </>
          ) : (
            <p className="muted">Chọn độc giả để kiểm tra điều kiện.</p>
          )}
        </Panel>
      </div>
      <MutationFeedback error={checkout.error} />
      {checkout.data && (
        <Panel title="Biên nhận mượn sách">
          <Badge tone="success">Hệ thống đã xác nhận</Badge>
          <Table
            headers={["Sách", "Mã vạch", "Hạn trả"]}
            rows={checkout.data.items.map((item) => {
              const copy = scanned.find((entry) => entry.copyId === item.copyId);
              return [copy?.title ?? "—", copy?.barcode ?? "—", formatDateTime(item.dueAt)];
            })}
            caption="Biên nhận mượn sách"
          />
          <div className="actions">
            <Button variant="secondary" icon="print" onClick={() => window.print()}>
              In biên nhận
            </Button>
            <Button onClick={reset}>Lập phiếu mới</Button>
          </div>
        </Panel>
      )}
      <Dialog
        open={confirm}
        title="Xác nhận cho mượn"
        pending={checkout.isPending}
        onClose={() => setConfirm(false)}
      >
        <p>
          Cho <strong>{reader?.full_name}</strong> mượn {scanned.length} cuốn. Hạn trả do hệ thống
          tính theo quy định đang hiệu lực.
        </p>
        <ul>
          {scanned.map((item) => (
            <li key={item.copyId}>{item.title}</li>
          ))}
        </ul>
        <div className="actions">
          <Button onClick={() => checkout.mutate()} disabled={checkout.isPending}>
            {checkout.isPending ? "Đang ghi nhận…" : "Xác nhận"}
          </Button>
          <Button variant="secondary" onClick={() => setConfirm(false)}>
            Quay lại
          </Button>
        </div>
      </Dialog>
    </div>
  );
}

function Returns() {
  const services = useServices();
  const session = useSession();
  const cache = useQueryClient();
  const key = useRef(createIdempotencyKey()).current;
  const canAssess = session.permissions.includes("assessment.propose");
  const [barcode, setBarcode] = useState("");
  const [condition, setCondition] = useState<"GOOD" | "DAMAGE" | "LOST">("GOOD");
  const [amount, setAmount] = useState("");
  const [reason, setReason] = useState("");
  const find = useMutation({
    mutationFn: async (code: string) =>
      (
        await services.circulation.get_loans({
          params: { query: { barcode: code, status: "OPEN", limit: 1 } },
        })
      ).data!.data[0],
  });
  const target = find.data;
  const save = useMutation({
    mutationFn: async () => {
      const body: components["schemas"]["ReturnRequest"] = {
        loanItemId: target!.loanItem.id,
        condition,
        ...(condition === "GOOD" ? {} : { assessment: { proposedAmount: amount, reason } }),
      };
      return (
        await services.circulation.post_returns({
          body,
          params: { header: { "Idempotency-Key": key.forPayload(body) } },
        })
      ).data!;
    },
    onSuccess: () => {
      key.reset();
      void cache.invalidateQueries({ queryKey: ["catalog"] });
      void cache.invalidateQueries({ queryKey: ["reader"] });
      void cache.invalidateQueries({ queryKey: ["loans"] });
    },
  });
  const next = () => {
    save.reset();
    find.reset();
    setBarcode("");
    setCondition("GOOD");
    setAmount("");
    setReason("");
  };
  return (
    <div className="stack">
      <Panel title="Tiếp nhận trả sách">
        {!save.isSuccess && (
          <form
            className="scan-form"
            onSubmit={(event) => {
              event.preventDefault();
              if (barcode.trim()) find.mutate(barcode.trim());
            }}
          >
            <Field
              label="Mã vạch bản sách"
              required
              value={barcode}
              onChange={(event) => setBarcode(event.target.value)}
            />
            <Button type="submit" variant="secondary" aria-busy={find.isPending}>
              Tìm khoản mượn
            </Button>
          </form>
        )}
        <MutationFeedback error={find.error} />
        {find.isSuccess && !target && (
          <Notice tone="warning">Bản sách này hiện không có khoản mượn đang mở.</Notice>
        )}
      </Panel>
      {target && !save.isSuccess && (
        <Panel title="Khoản mượn">
          <dl className="detail-list">
            <div>
              <dt>Phiếu</dt>
              <dd>{target.loan.loan_no}</dd>
            </div>
            <div>
              <dt>Mã vạch</dt>
              <dd>{target.copy.barcode}</dd>
            </div>
            <div>
              <dt>Hạn trả</dt>
              <dd>{formatDateTime(target.loanItem.due_at)}</dd>
            </div>
          </dl>
          <form
            onSubmit={(event) => {
              event.preventDefault();
              save.mutate();
            }}
          >
            <fieldset className="condition-selector">
              <legend>Tình trạng khi trả</legend>
              {(
                [
                  ["GOOD", "Tốt"],
                  ["DAMAGE", "Hỏng"],
                  ["LOST", "Mất"],
                ] as const
              ).map(([value, label]) => (
                <label key={value}>
                  <input
                    type="radio"
                    name="return-condition"
                    checked={condition === value}
                    disabled={value !== "GOOD" && !canAssess}
                    onChange={() => setCondition(value)}
                  />
                  {label}
                </label>
              ))}
            </fieldset>
            {!canAssess && (
              <p className="muted">Ghi nhận sách hỏng / mất cần quyền đề xuất phí.</p>
            )}
            {condition !== "GOOD" && (
              <div className="form-grid">
                <Field
                  label="Số tiền đề xuất (VND)"
                  inputMode="numeric"
                  pattern="[0-9]+"
                  required
                  value={amount}
                  onChange={(event) => setAmount(event.target.value)}
                />
                <Field
                  label="Lý do đề xuất"
                  required
                  value={reason}
                  onChange={(event) => setReason(event.target.value)}
                />
              </div>
            )}
            <Notice>
              Nhận trả không bị chặn bởi dư nợ hoặc hạn thẻ. Phí trễ do hệ thống tính; phí hỏng / mất
              chờ Quản lý xác nhận.
            </Notice>
            <div className="actions">
              <Button type="submit" disabled={save.isPending} aria-busy={save.isPending}>
                Ghi nhận trả sách
              </Button>
            </div>
            <MutationFeedback error={save.error} />
          </form>
        </Panel>
      )}
      {save.data && target && (
        <Panel title="Biên nhận trả sách">
          <Badge tone="success">Hệ thống đã xác nhận</Badge>
          <dl className="detail-list">
            <div>
              <dt>Phiếu</dt>
              <dd>{target.loan.loan_no}</dd>
            </div>
            <div>
              <dt>Mã vạch</dt>
              <dd>{target.copy.barcode}</dd>
            </div>
            <div>
              <dt>Trạng thái bản sách</dt>
              <dd>{save.data.copyStatus}</dd>
            </div>
            <div>
              <dt>Khoản phí phát sinh</dt>
              <dd>{save.data.charges.length}</dd>
            </div>
            {save.data.assessmentId && (
              <div>
                <dt>Đề xuất phí chờ duyệt</dt>
                <dd>Đã gửi Quản lý</dd>
              </div>
            )}
          </dl>
          <div className="actions">
            <Button variant="secondary" icon="print" onClick={() => window.print()}>
              In biên nhận
            </Button>
            <Button onClick={next}>Trả sách tiếp</Button>
          </div>
        </Panel>
      )}
    </div>
  );
}

/** Staff search for open loan items by card number or copy barcode. */
function LoanSearch({
  children,
}: {
  children: (rows: LoanRow[], refetch: () => void) => ReactNode;
}) {
  const services = useServices();
  const [mode, setMode] = useState<"cardNumber" | "barcode">("cardNumber");
  const [text, setText] = useState("");
  const [submitted, setSubmitted] = useState<{ mode: typeof mode; value: string }>();
  const result = useQuery({
    queryKey: ["loans", "search", submitted?.mode, submitted?.value],
    enabled: !!submitted,
    queryFn: async ({ signal }) =>
      (
        await services.circulation.get_loans({
          params: {
            query: {
              ...(submitted!.mode === "barcode"
                ? { barcode: submitted!.value }
                : { cardNumber: submitted!.value }),
              status: "OPEN",
              limit: 50,
            },
          },
          signal,
        })
      ).data!.data,
  });
  return (
    <div className="stack">
      <Panel title="Tra cứu khoản mượn đang mở">
        <form
          className="scan-form"
          onSubmit={(event) => {
            event.preventDefault();
            if (text.trim()) setSubmitted({ mode, value: text.trim() });
          }}
        >
          <fieldset className="condition-selector">
            <legend>Tra theo</legend>
            <label>
              <input
                type="radio"
                name="loan-search-mode"
                checked={mode === "cardNumber"}
                onChange={() => setMode("cardNumber")}
              />
              Số thẻ
            </label>
            <label>
              <input
                type="radio"
                name="loan-search-mode"
                checked={mode === "barcode"}
                onChange={() => setMode("barcode")}
              />
              Mã vạch
            </label>
          </fieldset>
          <Field
            label={mode === "barcode" ? "Mã vạch bản sách" : "Số thẻ độc giả"}
            required
            value={text}
            onChange={(event) => setText(event.target.value)}
          />
          <Button type="submit" variant="secondary">
            Tra cứu
          </Button>
        </form>
      </Panel>
      {result.isFetching && !result.data && <LoadingSkeleton />}
      {result.error && <ApiFailure error={result.error} retry={() => void result.refetch()} />}
      {result.data && !result.data.length && (
        <Notice tone="warning">Không có khoản mượn đang mở phù hợp.</Notice>
      )}
      {result.data && result.data.length > 0 && children(result.data, () => void result.refetch())}
    </div>
  );
}

function Renew() {
  const services = useServices();
  const cache = useQueryClient();
  const key = useRef(createIdempotencyKey()).current;
  const [target, setTarget] = useState<{ id: string; no: string; version: number; count: number }>();
  const renew = useMutation({
    mutationFn: async (loan: NonNullable<typeof target>) => {
      const body = { expectedVersion: loan.version };
      return (
        await services.circulation.post_loans_id_renewals({
          body,
          params: {
            path: { id: loan.id },
            header: { "Idempotency-Key": key.forPayload({ loan: loan.id, ...body }) },
          },
        })
      ).data!;
    },
    onSuccess: () => {
      key.reset();
      setTarget(undefined);
      void cache.invalidateQueries({ queryKey: ["loans"] });
    },
    onError: () => {
      // 409 / validation: keep the list, refresh versions, show the server message.
      setTarget(undefined);
      void cache.invalidateQueries({ queryKey: ["loans"] });
    },
  });
  return (
    <LoanSearch>
      {(rows) => {
        const groups = new Map<string, LoanRow[]>();
        for (const row of rows) groups.set(row.loan.id, [...(groups.get(row.loan.id) ?? []), row]);
        return (
          <>
            <Notice>
              Gia hạn áp dụng cho toàn bộ khoản đang mở của phiếu, hoặc không khoản nào. Hạn mới do
              hệ thống tính.
            </Notice>
            {[...groups.values()].map((items) => {
              const loan = items[0]!.loan;
              return (
                <Panel
                  key={loan.id}
                  title={`Phiếu ${loan.loan_no}`}
                  subtitle={`Đã gia hạn ${loan.renewal_count} lần`}
                >
                  <Table
                    caption={`Khoản mượn của phiếu ${loan.loan_no}`}
                    headers={["Mã vạch", "Hạn trả"]}
                    rows={items.map((item) => [item.copy.barcode, formatDateTime(item.loanItem.due_at)])}
                  />
                  <div className="actions">
                    <Button
                      onClick={() =>
                        setTarget({
                          id: loan.id,
                          no: loan.loan_no,
                          version: loan.version,
                          count: items.length,
                        })
                      }
                    >
                      Gia hạn phiếu
                    </Button>
                  </div>
                </Panel>
              );
            })}
            <MutationFeedback error={renew.error} success={renew.isSuccess}>
              Đã gia hạn phiếu. Hạn trả mới đã được cập nhật.
            </MutationFeedback>
            <Dialog
              open={!!target}
              title="Xác nhận gia hạn"
              pending={renew.isPending}
              onClose={() => setTarget(undefined)}
            >
              <p>
                Gia hạn {target?.count} khoản đang mở của phiếu <strong>{target?.no}</strong>?
              </p>
              <div className="actions">
                <Button
                  disabled={renew.isPending}
                  onClick={() => target && renew.mutate(target)}
                >
                  {renew.isPending ? "Đang gia hạn…" : "Xác nhận gia hạn"}
                </Button>
                <Button variant="secondary" onClick={() => setTarget(undefined)}>
                  Quay lại
                </Button>
              </div>
            </Dialog>
          </>
        );
      }}
    </LoanSearch>
  );
}

function LoanList() {
  return (
    <LoanSearch>
      {(rows) => (
        <Panel title="Khoản mượn đang mở">
          <Table
            caption="Khoản mượn đang mở"
            headers={["Phiếu", "Mã vạch", "Ngày mượn", "Hạn trả"]}
            rows={rows.map((row) => [
              row.loan.loan_no,
              row.copy.barcode,
              formatDateTime(row.loanItem.issued_at),
              formatDateTime(row.loanItem.due_at),
            ])}
          />
        </Panel>
      )}
    </LoanSearch>
  );
}

function LoanDetail({ loanId }: { loanId: string }) {
  const services = useServices();
  const result = useQuery({
    queryKey: ["loans", loanId],
    queryFn: async ({ signal }) =>
      (await services.circulation.get_loans_id({ params: { path: { id: loanId } }, signal }))
        .data!,
  });
  if (result.isPending) return <LoadingSkeleton />;
  if (result.error) return <ApiFailure error={result.error} retry={() => void result.refetch()} />;
  return (
    <Panel title={result.data.loan_no}>
      <dl className="detail-list">
        <div>
          <dt>Thời điểm lập</dt>
          <dd>{formatDateTime(result.data.issued_at)}</dd>
        </div>
        <div>
          <dt>Số lần gia hạn</dt>
          <dd>{result.data.renewal_count}</dd>
        </div>
      </dl>
    </Panel>
  );
}

export default function Circulation({ screen }: { screen: ScreenDefinition }) {
  const { loanId } = useParams();
  if (screen.group === "05") return <Returns />;
  if (screen.group === "06") return <Renew />;
  if (screen.id === "FE04.05" && loanId) return <LoanDetail loanId={loanId} />;
  if (screen.group === "04" && screen.id !== "FE04.01") return <LoanList />;
  return <Checkout />;
}
