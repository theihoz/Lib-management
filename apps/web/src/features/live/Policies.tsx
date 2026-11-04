import { useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router";
import { useServices, useSession } from "../../auth/session";
import { createIdempotencyKey } from "../../api/idempotency";
import { formatDateTime } from "../../lib/datetime";
import { formatVnd } from "../../lib/money";
import { Badge, Button, Dialog, Field, Notice, Panel, Table } from "../../ui/components";
import type { ScreenDefinition } from "../types";
import { ApiFailure, LoadingSkeleton, MutationFeedback } from "./common";
import {
  RULES_SCHEMA_VERSION,
  RULE_FIELDS,
  policyInForce,
  readRule,
  ruleText,
  toDraft,
  toRules,
  validateDraft,
  type RuleDraft,
} from "./policyRules";

function showRule(kind: string, value: unknown): string {
  const text = ruleText(value);
  if (!text) return "—";
  return kind === "money" ? formatVnd(text) : text;
}

const STATUS_TONE = { ACTIVE: "success", DRAFT: "neutral", SUPERSEDED: "warning" } as const;

function PolicyList() {
  const services = useServices();
  const session = useSession();
  const cache = useQueryClient();
  const key = useRef(createIdempotencyKey()).current;
  const canApprove = session.permissions.includes("policy.approve");
  const [target, setTarget] = useState<{ id: string; versionNo: number; from: string }>();
  const [now] = useState(() => Date.now());
  const list = useQuery({
    queryKey: ["policies"],
    queryFn: async ({ signal }) =>
      (await services.reports.get_policy_versions({ params: { query: { limit: 100 } }, signal }))
        .data!,
    staleTime: 0,
  });
  const approve = useMutation({
    mutationFn: async (policy: NonNullable<typeof target>) => {
      const body = { expectedVersion: policy.versionNo };
      return (
        await services.reports.post_policy_versions_id_approval({
          params: {
            path: { id: policy.id },
            header: { "Idempotency-Key": key.forPayload({ id: policy.id, ...body }) },
          },
          body,
        })
      ).data!;
    },
    onSettled: () => {
      setTarget(undefined);
      void cache.invalidateQueries({ queryKey: ["policies"] });
    },
    onSuccess: () => key.reset(),
  });
  if (list.isPending) return <LoadingSkeleton />;
  if (list.error) return <ApiFailure error={list.error} retry={() => void list.refetch()} />;
  const current = policyInForce(list.data.data, now);
  return (
    <div className="stack">
      <Notice>
        Quy định đã duyệt không thể sửa hoặc xóa. Phiên bản mới chỉ có hiệu lực từ thời điểm tương
        lai và không áp dụng hồi tố cho phiếu, thẻ hay phí đã phát sinh.
      </Notice>
      <Panel title="Các phiên bản quy định">
        <Table
          caption="Các phiên bản quy định"
          headers={["Phiên bản", "Trạng thái", "Hiệu lực từ", "Hiệu lực đến", "Thao tác"]}
          rows={list.data.data.map((policy) => [
            String(policy.version_no),
            policy.status === "DRAFT"
              ? "Bản nháp"
              : policy.status === "ACTIVE"
                ? new Date(policy.effective_from).getTime() > now
                  ? "Đã duyệt, chưa hiệu lực"
                  : "Đang hiệu lực"
                : "Đã thay thế",
            formatDateTime(policy.effective_from),
            policy.effective_to ? formatDateTime(policy.effective_to) : "Không giới hạn",
            policy.status === "DRAFT" && canApprove ? "Chờ duyệt" : "—",
          ])}
        />
        {canApprove &&
          list.data.data
            .filter((policy) => policy.status === "DRAFT")
            .map((policy) => (
              <div className="actions" key={policy.id}>
                <Badge tone={STATUS_TONE.DRAFT}>Bản nháp {policy.version_no}</Badge>
                <Button
                  variant="secondary"
                  onClick={() =>
                    setTarget({
                      id: policy.id,
                      versionNo: policy.version_no,
                      from: policy.effective_from,
                    })
                  }
                >
                  Duyệt bản {policy.version_no}
                </Button>
              </div>
            ))}
        <MutationFeedback error={approve.error} success={approve.isSuccess}>
          Đã duyệt phiên bản quy định.
        </MutationFeedback>
      </Panel>
      <Panel title="Quy định đang hiệu lực">
        {current ? (
          <dl className="detail-list">
            {RULE_FIELDS.map((field) => (
              <div key={field.key}>
                <dt>
                  {field.label} <span className="muted">({field.source})</span>
                </dt>
                <dd>{showRule(field.kind, readRule(current.rules, field.key))}</dd>
              </div>
            ))}
          </dl>
        ) : (
          <Notice tone="warning">Chưa có quy định đang hiệu lực.</Notice>
        )}
      </Panel>
      <Dialog
        open={!!target}
        title="Xác nhận duyệt quy định"
        pending={approve.isPending}
        onClose={() => setTarget(undefined)}
      >
        <p>
          Duyệt bản {target?.versionNo}, hiệu lực từ{" "}
          <strong>{target ? formatDateTime(target.from) : ""}</strong>. Không thể sửa sau khi duyệt.
        </p>
        <div className="actions">
          <Button disabled={approve.isPending} onClick={() => target && approve.mutate(target)}>
            {approve.isPending ? "Đang duyệt…" : "Xác nhận duyệt"}
          </Button>
          <Button variant="secondary" onClick={() => setTarget(undefined)}>
            Quay lại
          </Button>
        </div>
      </Dialog>
    </div>
  );
}

function PolicyCreate() {
  const services = useServices();
  const [now] = useState(() => Date.now());
  const list = useQuery({
    queryKey: ["policies"],
    queryFn: async ({ signal }) =>
      (await services.reports.get_policy_versions({ params: { query: { limit: 100 } }, signal }))
        .data!,
    staleTime: 0,
  });
  if (list.isPending) return <LoadingSkeleton />;
  if (list.error) return <ApiFailure error={list.error} retry={() => void list.refetch()} />;
  // QĐ16: show the values in force before the Manager edits them.
  const current = policyInForce(list.data.data, now)?.rules;
  return <PolicyDraftForm current={current} openedAt={now} />;
}

function PolicyDraftForm({
  current,
  openedAt,
}: {
  current: Record<string, unknown> | undefined;
  openedAt: number;
}) {
  const services = useServices();
  const navigate = useNavigate();
  const key = useRef(createIdempotencyKey()).current;
  const [from, setFrom] = useState("");
  const [draft, setDraft] = useState<RuleDraft>(() => toDraft(current));
  const [submitted, setSubmitted] = useState(false);
  const errors = validateDraft(draft);
  const invalid = Object.keys(errors).length > 0;
  const create = useMutation({
    mutationFn: async () => {
      const body = {
        // Datetime-local value interpreted in library time (Asia/Ho_Chi_Minh).
        effectiveFrom: new Date(`${from}:00+07:00`).toISOString(),
        rulesSchemaVersion: RULES_SCHEMA_VERSION,
        rules: toRules(draft),
      };
      return (
        await services.reports.post_policy_versions({
          body,
          params: { header: { "Idempotency-Key": key.forPayload(body) } },
        })
      ).data!;
    },
    onSuccess: () => {
      key.reset();
      void navigate("/manager/policies");
    },
  });
  const past = from !== "" && new Date(`${from}:00+07:00`).getTime() <= openedAt;
  const changed = RULE_FIELDS.filter(
    (field) => current && ruleText(readRule(current, field.key)) !== draft[field.key],
  );
  return (
    <Panel title="Tạo bản nháp quy định">
      <form
        noValidate
        onSubmit={(event) => {
          event.preventDefault();
          setSubmitted(true);
          if (!past && !invalid) create.mutate();
        }}
      >
        <Field
          label="Hiệu lực từ (giờ thư viện)"
          type="datetime-local"
          required
          value={from}
          error={past ? "Thời điểm hiệu lực phải ở tương lai." : undefined}
          onChange={(event) => setFrom(event.target.value)}
        />
        <div className="form-grid">
          {RULE_FIELDS.map((field) => (
            <Field
              key={field.key}
              label={`${field.label} (${field.source})`}
              inputMode={field.kind === "text" ? undefined : "numeric"}
              required
              value={draft[field.key] ?? ""}
              hint={
                current
                  ? `Hiện tại: ${showRule(field.kind, readRule(current, field.key))}`
                  : undefined
              }
              error={errors[field.key]}
              onChange={(event) => setDraft({ ...draft, [field.key]: event.target.value })}
            />
          ))}
        </div>
        <Notice>
          Bản nháp chỉ có hiệu lực sau khi được duyệt và từ thời điểm đã chọn; phiếu, thẻ và phí đã
          phát sinh giữ quy định cũ. Phí hỏng/mất là mức đề xuất, Quản lý vẫn xác nhận từng khoản.
        </Notice>
        {changed.length > 0 && (
          <Table
            caption="So sánh với quy định đang hiệu lực"
            headers={["Quy định", "Hiện tại", "Bản nháp"]}
            rows={changed.map((field) => [
              field.label,
              showRule(field.kind, current && readRule(current, field.key)),
              showRule(field.kind, draft[field.key]),
            ])}
          />
        )}
        <MutationFeedback error={create.error} />
        <div className="actions">
          <Button
            type="submit"
            disabled={create.isPending || past || (submitted && invalid)}
            aria-busy={create.isPending}
          >
            Lưu bản nháp
          </Button>
        </div>
      </form>
    </Panel>
  );
}

export default function Policies({ screen }: { screen: ScreenDefinition }) {
  return screen.id === "FE09.06" ? <PolicyCreate /> : <PolicyList />;
}
