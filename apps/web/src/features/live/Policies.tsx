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

// Rules v1 are fixed by decisions C01–C09 (server rejects anything else).
const RULES_V1 = {
  minReaderAge: 12,
  maxReaderAge: 55,
  cardValidityMonths: 6,
  maxBooksPerLoan: 4,
  initialLoanDays: 4,
  maxRenewals: 1,
  renewalDays: 4,
  overdueFinePerDay: "1000",
  allowedOutstandingBalance: "0",
  publicationYearWindow: 8,
  readyHoldDays: 3,
  damageLostAssessment: "MANUAL_APPROVAL",
};
const RULE_LABELS: [keyof typeof RULES_V1, string][] = [
  ["minReaderAge", "Tuổi tối thiểu"],
  ["maxReaderAge", "Tuổi tối đa"],
  ["cardValidityMonths", "Hạn thẻ (tháng)"],
  ["maxBooksPerLoan", "Số cuốn tối đa mỗi phiếu"],
  ["initialLoanDays", "Số ngày mượn"],
  ["maxRenewals", "Số lần gia hạn"],
  ["renewalDays", "Số ngày mỗi lần gia hạn"],
  ["overdueFinePerDay", "Phí trễ mỗi ngày mỗi cuốn"],
  ["allowedOutstandingBalance", "Dư nợ cho phép"],
  ["publicationYearWindow", "Cửa sổ năm xuất bản"],
];
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
      <Panel title="Quy tắc hiện hành (v1)">
        <dl className="detail-list">
          {RULE_LABELS.map(([name, label]) => (
            <div key={name}>
              <dt>{label}</dt>
              <dd>
                {name === "overdueFinePerDay" || name === "allowedOutstandingBalance"
                  ? formatVnd(String(RULES_V1[name]))
                  : String(RULES_V1[name])}
              </dd>
            </div>
          ))}
        </dl>
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
  const navigate = useNavigate();
  const key = useRef(createIdempotencyKey()).current;
  const [from, setFrom] = useState("");
  const create = useMutation({
    mutationFn: async () => {
      const body = {
        // Datetime-local value interpreted in library time (Asia/Ho_Chi_Minh).
        effectiveFrom: new Date(`${from}:00+07:00`).toISOString(),
        rulesSchemaVersion: 1,
        rules: RULES_V1,
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
  const [openedAt] = useState(() => Date.now());
  const past = from !== "" && new Date(`${from}:00+07:00`).getTime() <= openedAt;
  return (
    <Panel title="Tạo bản nháp quy định">
      <form
        onSubmit={(event) => {
          event.preventDefault();
          if (!past) create.mutate();
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
        <Notice>
          Bản nháp dùng quy tắc v1 theo các quyết định đã duyệt (C01–C09). Quy tắc không chỉnh sửa
          tại đây.
        </Notice>
        <MutationFeedback error={create.error} />
        <div className="actions">
          <Button type="submit" disabled={create.isPending || past} aria-busy={create.isPending}>
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
