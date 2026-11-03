import { useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate, useParams } from "react-router";
import { useServices } from "../../auth/session";
import { createIdempotencyKey } from "../../api/idempotency";
import { formatDateTime } from "../../lib/datetime";
import { formatVnd } from "../../lib/money";
import { Badge, Button, Field, Notice, Panel, Table } from "../../ui/components";
import type { ScreenDefinition } from "../types";
import { ApiFailure, LoadingSkeleton, MutationFeedback } from "./common";
import { ReaderPicker } from "./ReaderPicker";
import type { Reader } from "./ReaderPicker";

const VND = /^[0-9]+$/;

function useReaderCharges(reader: Reader | undefined) {
  const services = useServices();
  return useQuery({
    queryKey: ["reader", reader?.id, "charges"],
    enabled: !!reader,
    staleTime: 0,
    queryFn: async ({ signal }) =>
      (
        await services.finance.get_fine_charges({
          params: { query: { readerId: reader!.id, limit: 100 } },
          signal,
        })
      ).data!.data,
  });
}

/** Reader selection that keeps the chosen reader visible with a way to change it. */
function ReaderStep({
  reader,
  onChange,
}: {
  reader: Reader | undefined;
  onChange: (reader: Reader | undefined) => void;
}) {
  return (
    <Panel title="Độc giả">
      {reader ? (
        <div className="reader-strip" aria-live="polite">
          <strong>{reader.full_name}</strong> · {reader.reader_code}
          <Button variant="ghost" onClick={() => onChange(undefined)}>
            Đổi độc giả
          </Button>
        </div>
      ) : (
        <ReaderPicker onPick={onChange} />
      )}
    </Panel>
  );
}

function Charges() {
  const [reader, setReader] = useState<Reader>();
  const charges = useReaderCharges(reader);
  return (
    <div className="stack">
      <ReaderStep reader={reader} onChange={setReader} />
      {charges.isFetching && !charges.data && <LoadingSkeleton />}
      {charges.error && <ApiFailure error={charges.error} retry={() => void charges.refetch()} />}
      {charges.data && (
        <Panel title="Khoản phí">
          <Table
            caption="Khoản phí của độc giả"
            headers={["Lý do", "Số tiền", "Ngày ghi nhận"]}
            rows={charges.data.map((charge) => [
              charge.reason,
              formatVnd(charge.assessed_amount),
              formatDateTime(charge.created_at),
            ])}
          />
        </Panel>
      )}
    </div>
  );
}

/** Pick a charge of the selected reader, then collect money or waive it. */
function ChargeAction({ mode }: { mode: "payment" | "waiver" }) {
  const services = useServices();
  const cache = useQueryClient();
  const key = useRef(createIdempotencyKey()).current;
  const [reader, setReader] = useState<Reader>();
  const [chargeId, setChargeId] = useState("");
  const [amount, setAmount] = useState("");
  const [method, setMethod] = useState<"CASH" | "TRANSFER_RECORD">("CASH");
  const [reference, setReference] = useState("");
  const [reason, setReason] = useState("");
  const charges = useReaderCharges(reader);
  const invalid = amount !== "" && !VND.test(amount);
  const save = useMutation({
    mutationFn: async () => {
      if (mode === "payment") {
        const body = {
          readerId: reader!.id,
          amount,
          method,
          ...(reference ? { reference } : {}),
          allocations: [{ chargeId, amount }],
        };
        return services.finance.post_payments({
          body,
          params: { header: { "Idempotency-Key": key.forPayload(body) } },
        });
      }
      const body = { amount, reason };
      return services.finance.post_fine_charges_id_waivers({
        body,
        params: {
          path: { id: chargeId },
          header: { "Idempotency-Key": key.forPayload({ chargeId, ...body }) },
        },
      });
    },
    onSuccess: () => {
      key.reset();
      setAmount("");
      setReason("");
      setReference("");
      void cache.invalidateQueries({ queryKey: ["reader"] });
    },
  });
  return (
    <div className="stack">
      <ReaderStep
        reader={reader}
        onChange={(next) => {
          setReader(next);
          setChargeId("");
        }}
      />
      {reader && (
        <Panel title={mode === "payment" ? "Thu tiền" : "Miễn phí"}>
          {charges.error && <ApiFailure error={charges.error} />}
          {charges.data && !charges.data.length && (
            <Notice tone="warning">Độc giả này chưa có khoản phí nào.</Notice>
          )}
          <form
            onSubmit={(event) => {
              event.preventDefault();
              if (!invalid && chargeId) save.mutate();
            }}
          >
            <div className="form-grid">
              <div className="field">
                <label htmlFor="charge-select">Khoản phí</label>
                <select
                  id="charge-select"
                  required
                  value={chargeId}
                  onChange={(event) => setChargeId(event.target.value)}
                >
                  <option value="">Chọn khoản phí…</option>
                  {charges.data?.map((charge) => (
                    <option key={charge.id} value={charge.id}>
                      {charge.reason} — {formatVnd(charge.assessed_amount)}
                    </option>
                  ))}
                </select>
              </div>
              <Field
                label="Số tiền (VND)"
                inputMode="numeric"
                required
                value={amount}
                error={invalid ? "Chỉ nhập số nguyên VND." : undefined}
                onChange={(event) => setAmount(event.target.value)}
              />
              {mode === "payment" ? (
                <>
                  <div className="field">
                    <label htmlFor="pay-method">Hình thức</label>
                    <select
                      id="pay-method"
                      value={method}
                      onChange={(event) => setMethod(event.target.value as typeof method)}
                    >
                      <option value="CASH">Tiền mặt</option>
                      <option value="TRANSFER_RECORD">Ghi nhận chuyển khoản</option>
                    </select>
                  </div>
                  <Field
                    label="Tham chiếu (không bắt buộc)"
                    value={reference}
                    onChange={(event) => setReference(event.target.value)}
                  />
                </>
              ) : (
                <Field
                  label="Lý do (bắt buộc)"
                  required
                  value={reason}
                  onChange={(event) => setReason(event.target.value)}
                />
              )}
            </div>
            <p className="data-description">
              Hệ thống từ chối số tiền vượt dư nợ của khoản phí. Mỗi thao tác được ghi sổ và không
              thể xóa.
            </p>
            <MutationFeedback error={save.error} success={save.isSuccess}>
              {mode === "payment" ? "Đã ghi nhận thanh toán." : "Đã ghi nhận miễn phí."}
            </MutationFeedback>
            <div className="actions">
              <Button type="submit" disabled={save.isPending || invalid} aria-busy={save.isPending}>
                {mode === "payment" ? "Xác nhận đã nhận tiền" : "Xác nhận miễn phí"}
              </Button>
            </div>
          </form>
        </Panel>
      )}
    </div>
  );
}

function useAssessments() {
  const services = useServices();
  return useQuery({
    queryKey: ["assessments"],
    staleTime: 0,
    queryFn: async ({ signal }) =>
      (await services.finance.get_charge_assessments({ params: { query: { limit: 100 } }, signal }))
        .data!.data,
  });
}

const KIND = { DAMAGE: "Hỏng", LOST: "Mất" } as const;
const STATE = {
  PENDING: "Chờ quyết định",
  ASSESSED: "Đã tính phí",
  CLOSED_NO_CHARGE: "Kết thúc, không thu",
} as const;

function AssessmentList() {
  const navigate = useNavigate();
  const list = useAssessments();
  if (list.isPending) return <LoadingSkeleton />;
  if (list.error) return <ApiFailure error={list.error} retry={() => void list.refetch()} />;
  const rows = list.data;
  return (
    <Panel title="Đề xuất phí hỏng / mất">
      <Table
        caption="Đề xuất phí hỏng / mất"
        headers={["Loại", "Trạng thái", "Đề xuất", "Lý do"]}
        rows={rows.map((row) => [
          KIND[row.kind],
          STATE[row.status],
          formatVnd(row.proposed_amount),
          row.reason,
        ])}
        onRow={(index) => {
          const row = rows[index];
          if (row) void navigate(`/manager/charge-assessments/${row.id}`);
        }}
      />
    </Panel>
  );
}

function AssessmentDecision({ id }: { id: string }) {
  const services = useServices();
  const cache = useQueryClient();
  const key = useRef(createIdempotencyKey()).current;
  const list = useAssessments();
  const [amount, setAmount] = useState("");
  const [reason, setReason] = useState("");
  const row = list.data?.find((item) => item.id === id);
  const invalid = amount !== "" && !VND.test(amount);
  const decide = useMutation({
    mutationFn: async () => {
      const body = { expectedVersion: row!.version, amount, reason };
      return services.finance.post_charge_assessments_id_decisions({
        body,
        params: { path: { id }, header: { "Idempotency-Key": key.forPayload({ id, ...body }) } },
      });
    },
    onSuccess: () => key.reset(),
    // A 409 means another manager decided first: reload and keep the typed input.
    onSettled: () => void cache.invalidateQueries({ queryKey: ["assessments"] }),
  });
  if (list.isPending) return <LoadingSkeleton />;
  if (list.error) return <ApiFailure error={list.error} retry={() => void list.refetch()} />;
  if (!row) return <Notice tone="warning">Không tìm thấy đề xuất này.</Notice>;
  const pending = row.status === "PENDING";
  return (
    <div className="stack">
      <Panel title={`Đề xuất phí ${KIND[row.kind].toLowerCase()}`}>
        <dl className="detail-list">
          <div>
            <dt>Trạng thái</dt>
            <dd>
              <Badge tone={pending ? "warning" : "success"}>{STATE[row.status]}</Badge>
            </dd>
          </div>
          <div>
            <dt>Số tiền đề xuất</dt>
            <dd>{formatVnd(row.proposed_amount)}</dd>
          </div>
          <div>
            <dt>Lý do đề xuất</dt>
            <dd>{row.reason}</dd>
          </div>
          {row.approved_amount != null && (
            <div>
              <dt>Số tiền đã duyệt</dt>
              <dd>{formatVnd(row.approved_amount)}</dd>
            </div>
          )}
        </dl>
      </Panel>
      {pending && (
        <Panel title="Quyết định">
          <form
            onSubmit={(event) => {
              event.preventDefault();
              if (!invalid) decide.mutate();
            }}
          >
            <div className="form-grid">
              <Field
                label="Số tiền xác nhận (0 = kết thúc không thu)"
                inputMode="numeric"
                required
                value={amount}
                error={invalid ? "Chỉ nhập số nguyên VND." : undefined}
                onChange={(event) => setAmount(event.target.value)}
              />
              <Field
                label="Lý do quyết định"
                required
                value={reason}
                onChange={(event) => setReason(event.target.value)}
              />
            </div>
            <MutationFeedback error={decide.error} success={decide.isSuccess}>
              Đã ghi nhận quyết định.
            </MutationFeedback>
            <div className="actions">
              <Button
                type="submit"
                disabled={decide.isPending || invalid}
                aria-busy={decide.isPending}
              >
                Xác nhận quyết định
              </Button>
            </div>
          </form>
        </Panel>
      )}
    </div>
  );
}

export default function Finance({ screen }: { screen: ScreenDefinition }) {
  const { assessmentId } = useParams();
  if (screen.id === "FE07.02") return <ChargeAction mode="payment" />;
  if (screen.id === "FE07.05") return <ChargeAction mode="waiver" />;
  if (screen.id === "FE07.03") return <AssessmentList />;
  if (screen.id === "FE07.04" && assessmentId) return <AssessmentDecision id={assessmentId} />;
  return <Charges />;
}
