import { useRef, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useNavigate, useParams } from "react-router";
import { useServices } from "../../auth/session";
import { createIdempotencyKey } from "../../api/idempotency";
import { ApiError } from "../../api/errors";
import { formatDateTime } from "../../lib/datetime";
import { Badge, Button, Field, Notice, Panel, Stats, Table } from "../../ui/components";
import type { ScreenDefinition } from "../types";
import { ApiFailure, LoadingSkeleton, MutationFeedback } from "./common";

const TYPES = [
  ["LENDING_SUMMARY", "Tổng hợp mượn trả"],
  ["OVERDUE", "Khoản mượn quá hạn"],
] as const;
const FINAL = ["SUCCEEDED", "DEAD", "FAILED"];

/** Library-local date (Asia/Ho_Chi_Minh) at 00:00 as an RFC 3339 instant. */
function localStart(date: string, plusDays = 0): string {
  const start = new Date(`${date}T00:00:00+07:00`).getTime();
  return new Date(start + plusDays * 86_400_000).toISOString();
}

/** Polls a job until it reaches a final state. */
function useJob(jobId: string | undefined) {
  const services = useServices();
  return useQuery({
    queryKey: ["reports", "job", jobId],
    enabled: !!jobId,
    queryFn: async ({ signal }) =>
      (await services.reports.get_jobs_id({ params: { path: { id: jobId! } }, signal })).data!,
    refetchInterval: (query) =>
      query.state.data && FINAL.includes(query.state.data.status) ? false : 2000,
    staleTime: 0,
  });
}

function RequestForm({ kind, onCreated }: { kind: "report" | "export"; onCreated: (id: string) => void }) {
  const services = useServices();
  const key = useRef(createIdempotencyKey()).current;
  const [type, setType] = useState<(typeof TYPES)[number][0]>("LENDING_SUMMARY");
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const invalid = from !== "" && to !== "" && to < from;
  const create = useMutation({
    mutationFn: async () => {
      const options = {
        body: {
          reportType: type,
          // Interval [from, to): the chosen end date is inclusive for the user.
          filters: { from: localStart(from), to: localStart(to, 1) },
        },
        params: { header: { "Idempotency-Key": "" } },
      };
      options.params.header["Idempotency-Key"] = key.forPayload(options.body);
      const response =
        kind === "export"
          ? await services.reports.post_export_jobs(options)
          : await services.reports.post_report_jobs(options);
      return response.data!;
    },
    onSuccess: (accepted) => {
      key.reset();
      onCreated(accepted.jobId);
    },
  });
  return (
    <Panel title={kind === "export" ? "Yêu cầu xuất CSV" : "Tạo báo cáo"}>
      <form
        onSubmit={(event) => {
          event.preventDefault();
          if (!invalid) create.mutate();
        }}
      >
        <div className="form-grid">
          <div className="field">
            <label htmlFor="report-type">Loại báo cáo</label>
            <select
              id="report-type"
              value={type}
              onChange={(event) => setType(event.target.value as typeof type)}
            >
              {TYPES.map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </div>
          <Field label="Từ ngày" type="date" required value={from} onChange={(e) => setFrom(e.target.value)} />
          <Field
            label="Đến ngày (gồm cả ngày này)"
            type="date"
            required
            value={to}
            error={invalid ? "Ngày kết thúc phải từ ngày bắt đầu trở đi." : undefined}
            onChange={(e) => setTo(e.target.value)}
          />
        </div>
        <p className="data-description">Khoảng thời gian tính theo giờ thư viện (Asia/Ho_Chi_Minh).</p>
        <MutationFeedback error={create.error} />
        <div className="actions">
          <Button type="submit" disabled={create.isPending || invalid} aria-busy={create.isPending}>
            {create.isPending ? "Đang gửi…" : kind === "export" ? "Yêu cầu xuất CSV" : "Tạo báo cáo"}
          </Button>
        </div>
      </form>
    </Panel>
  );
}

function JobBadge({ status }: { status: string }) {
  const tone = status === "SUCCEEDED" ? "success" : FINAL.includes(status) ? "danger" : "warning";
  const label: Record<string, string> = {
    QUEUED: "Đang chờ xử lý",
    RUNNING: "Đang xử lý",
    SUCCEEDED: "Hoàn tất",
    FAILED: "Thất bại",
    DEAD: "Thất bại",
  };
  return <Badge tone={tone}>{label[status] ?? status}</Badge>;
}

function ReportResultView({ jobId }: { jobId: string }) {
  const services = useServices();
  const [cursor, setCursor] = useState<string>();
  const result = useQuery({
    queryKey: ["reports", "result", jobId, cursor],
    queryFn: async ({ signal }) =>
      (
        await services.reports.get_report_jobs_id_result({
          params: { path: { id: jobId }, query: { cursor, limit: 20 } },
          signal,
        })
      ).data!,
    retry: (count, error) => !(error instanceof ApiError && [404, 409, 410].includes(error.status)) && count < 2,
    placeholderData: (previous) => previous,
  });
  if (result.isPending) return <LoadingSkeleton />;
  if (result.error) {
    const gone = result.error instanceof ApiError && result.error.status === 410;
    return gone ? (
      <Notice tone="warning">Kết quả báo cáo đã hết hạn lưu trữ. Hãy tạo báo cáo mới.</Notice>
    ) : (
      <ApiFailure error={result.error} retry={() => void result.refetch()} />
    );
  }
  const data = result.data;
  const columns = data.rows[0] ? Object.keys(data.rows[0]) : [];
  return (
    <div className="stack">
      <Notice>
        Dữ liệu tại thời điểm {formatDateTime(data.as_of)} (không phải thời điểm yêu cầu).
      </Notice>
      <Stats
        items={[
          { label: "Lượt mượn", value: String(data.metrics.loan_items_issued) },
          { label: "Lượt trả", value: String(data.metrics.returns_received) },
          { label: "Độc giả mượn", value: String(data.metrics.distinct_borrowers) },
          { label: "Đang quá hạn", value: String(data.metrics.open_overdue_items) },
        ]}
      />
      <Panel title="Chi tiết">
        <Table
          caption="Chi tiết báo cáo"
          headers={columns}
          rows={data.rows.map((row) => columns.map((column) => String(row[column] ?? "—")))}
        />
        <div className="actions">
          {cursor && (
            <Button variant="secondary" onClick={() => setCursor(undefined)}>
              Về trang đầu
            </Button>
          )}
          {data.nextCursor && (
            <Button variant="secondary" onClick={() => setCursor(data.nextCursor ?? undefined)}>
              Trang sau
            </Button>
          )}
        </div>
      </Panel>
    </div>
  );
}

function ReportCreate() {
  const navigate = useNavigate();
  return <RequestForm kind="report" onCreated={(id) => void navigate(`/manager/reports/${id}`)} />;
}

function ReportDetail({ jobId }: { jobId: string }) {
  const job = useJob(jobId);
  if (job.isPending) return <LoadingSkeleton />;
  if (job.error) return <ApiFailure error={job.error} retry={() => void job.refetch()} />;
  return (
    <div className="stack">
      <Panel title="Trạng thái báo cáo">
        <JobBadge status={job.data.status} />
        {job.data.status === "DEAD" || job.data.status === "FAILED" ? (
          <Notice tone="danger">Không thể tạo báo cáo. Hãy thử tạo lại.</Notice>
        ) : null}
      </Panel>
      {job.data.status === "SUCCEEDED" && <ReportResultView jobId={jobId} />}
    </div>
  );
}

function ExportPage() {
  const services = useServices();
  const [jobId, setJobId] = useState<string>();
  const job = useJob(jobId);
  const download = useMutation({
    mutationFn: async () => {
      const blob = (
        await services.reports.get_export_jobs_id_content({ params: { path: { id: jobId! } } })
      ).data as Blob;
      const url = URL.createObjectURL(blob);
      try {
        const link = document.createElement("a");
        link.href = url;
        link.download = `bao-cao-${jobId}.csv`;
        document.body.append(link);
        link.click();
        link.remove();
      } finally {
        // Revoke after the browser has started the download.
        setTimeout(() => URL.revokeObjectURL(url), 10_000);
      }
    },
  });
  const expired = download.error instanceof ApiError && download.error.status === 410;
  return (
    <div className="stack">
      <RequestForm kind="export" onCreated={setJobId} />
      {jobId && (
        <Panel title="Tệp CSV">
          {job.isPending ? (
            <LoadingSkeleton />
          ) : job.error ? (
            <ApiFailure error={job.error} retry={() => void job.refetch()} />
          ) : (
            <>
              <JobBadge status={job.data.status} />
              {["DEAD", "FAILED"].includes(job.data.status) && (
                <Notice tone="danger">Không thể tạo tệp. Hãy yêu cầu lại.</Notice>
              )}
              {job.data.status === "SUCCEEDED" && (
                <div className="actions">
                  <Button
                    icon="download"
                    disabled={download.isPending}
                    onClick={() => download.mutate()}
                  >
                    Tải CSV
                  </Button>
                </div>
              )}
            </>
          )}
          {expired ? (
            <Notice tone="warning">Tệp đã hết hạn. Hãy yêu cầu xuất lại.</Notice>
          ) : (
            <MutationFeedback error={download.error} />
          )}
        </Panel>
      )}
    </div>
  );
}

export default function Reports({ screen }: { screen: ScreenDefinition }) {
  const { reportId } = useParams();
  if (screen.id === "FE09.04") return <ExportPage />;
  if (screen.id === "FE09.03" && reportId) return <ReportDetail jobId={reportId} />;
  return <ReportCreate />;
}
