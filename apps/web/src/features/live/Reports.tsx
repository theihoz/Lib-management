import { useRef, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useNavigate, useParams } from "react-router";
import { useServices } from "../../auth/session";
import { createIdempotencyKey } from "../../api/idempotency";
import { ApiError } from "../../api/errors";
import { formatDateTime } from "../../lib/datetime";
import { formatVnd } from "../../lib/money";
import { Badge, Button, Field, Notice, Panel, Stats, Table } from "../../ui/components";
import type { ScreenDefinition } from "../types";
import { ApiFailure, LoadingSkeleton, MutationFeedback } from "./common";

// BM08 sections (report) and requirement 20 CSVs (export only).
const REPORT_TYPES = [
  ["OVERVIEW", "Tổng quan (BM08 §I)"],
  ["TOP_BOOKS", "Top sách được mượn nhiều (§II)"],
  ["ACTIVE_READERS", "Độc giả tích cực (§III)"],
  ["LOAN_TREND", "Lượt mượn theo thời gian (§IV)"],
  ["INVENTORY", "Tồn kho theo đầu sách"],
  ["OVERDUE", "Khoản mượn quá hạn"],
  ["LENDING_SUMMARY", "Tổng hợp mượn trả theo đầu sách"],
] as const;
const EXPORT_TYPES = [
  ["LOAN_CSV", "CSV phiếu mượn"],
  ["FINE_CSV", "CSV phạt"],
  ...REPORT_TYPES,
] as const;
type ReportType = (typeof EXPORT_TYPES)[number][0];
const RANKED: string[] = ["TOP_BOOKS", "ACTIVE_READERS"];
const FINAL = ["SUCCEEDED", "DEAD", "FAILED"];
const COLUMN_LABELS: Record<string, string> = {
  edition_id: "Mã ấn bản",
  title: "Tên sách",
  categories: "Thể loại",
  loan_count: "Số lượt mượn",
  issued_count: "Lượt mượn",
  returned_count: "Lượt trả",
  reader_id: "Mã định danh",
  reader_code: "Mã độc giả",
  full_name: "Họ và tên",
  fines_amount: "Tiền phạt",
  period: "Thời gian",
  loans_issued: "Số lượt mượn",
  returns_received: "Số lượt trả",
  total_copies: "Tổng bản sao",
  available: "Sẵn sàng",
  on_loan: "Đang mượn",
  held: "Đang giữ chỗ",
  unavailable: "Hỏng/mất/thanh lý",
  loan_item_id: "Mục mượn",
  loan_no: "Phiếu mượn",
  barcode: "Mã vạch",
  due_at: "Hạn trả",
  late_days: "Số ngày trễ",
};
const MONEY_COLUMNS = new Set(["fines_amount", "assessed_amount", "balance"]);

/** Today in library time as YYYY-MM-DD (QĐ13 upper bound). */
function libraryToday(): string {
  return new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Ho_Chi_Minh" }).format(new Date());
}

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

function RequestForm({
  kind,
  onCreated,
}: {
  kind: "report" | "export";
  onCreated: (id: string) => void;
}) {
  const services = useServices();
  const key = useRef(createIdempotencyKey()).current;
  const types = kind === "export" ? EXPORT_TYPES : REPORT_TYPES;
  const [type, setType] = useState<ReportType>(types[0][0]);
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [granularity, setGranularity] = useState<"day" | "week" | "month">("day");
  const [limit, setLimit] = useState("10");
  const [today] = useState(libraryToday);
  // QĐ13: Từ ngày ≤ Đến ngày ≤ ngày hiện tại.
  const reversed = from !== "" && to !== "" && to < from;
  const future = to !== "" && to > today;
  const badLimit =
    RANKED.includes(type) && (!/^\d+$/.test(limit) || Number(limit) < 1 || Number(limit) > 100);
  const invalid = reversed || future || badLimit;
  const create = useMutation({
    mutationFn: async () => {
      const options = {
        body: {
          reportType: type,
          // Interval [from, to): the chosen end date is inclusive for the user.
          filters: {
            from: localStart(from),
            to: localStart(to, 1),
            granularity,
            limit: RANKED.includes(type) ? Number(limit) : 10,
          },
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
              {types.map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </div>
          <Field
            label="Từ ngày"
            type="date"
            required
            value={from}
            max={today}
            onChange={(e) => setFrom(e.target.value)}
          />
          <Field
            label="Đến ngày (gồm cả ngày này)"
            type="date"
            required
            value={to}
            max={today}
            error={
              reversed
                ? "Ngày kết thúc phải từ ngày bắt đầu trở đi."
                : future
                  ? "Ngày kết thúc không được sau hôm nay (QĐ13)."
                  : undefined
            }
            onChange={(e) => setTo(e.target.value)}
          />
          {type === "LOAN_TREND" && (
            <div className="field">
              <label htmlFor="report-granularity">Gom theo</label>
              <select
                id="report-granularity"
                value={granularity}
                onChange={(event) => setGranularity(event.target.value as typeof granularity)}
              >
                <option value="day">Ngày</option>
                <option value="week">Tuần</option>
                <option value="month">Tháng</option>
              </select>
            </div>
          )}
          {RANKED.includes(type) && (
            <Field
              label="Số dòng xếp hạng (1–100)"
              inputMode="numeric"
              value={limit}
              error={badLimit ? "Nhập số nguyên từ 1 đến 100." : undefined}
              onChange={(event) => setLimit(event.target.value)}
            />
          )}
        </div>
        <p className="data-description">
          Khoảng thời gian tính theo giờ thư viện (Asia/Ho_Chi_Minh).
        </p>
        <MutationFeedback error={create.error} />
        <div className="actions">
          <Button type="submit" disabled={create.isPending || invalid} aria-busy={create.isPending}>
            {create.isPending
              ? "Đang gửi…"
              : kind === "export"
                ? "Yêu cầu xuất CSV"
                : "Tạo báo cáo"}
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
    retry: (count, error) =>
      !(error instanceof ApiError && [404, 409, 410].includes(error.status)) && count < 2,
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
  const cellText = (value: unknown): string => {
    if (value === null || value === undefined) return "—";
    if (typeof value === "string") return value;
    if (typeof value === "number" || typeof value === "boolean") return String(value);
    return JSON.stringify(value);
  };
  const columns = data.rows[0] ? Object.keys(data.rows[0]) : [];
  const shown = (column: string, value: unknown) =>
    MONEY_COLUMNS.has(column) && typeof value === "string" ? formatVnd(value) : cellText(value);
  const trend =
    data.report_type === "LOAN_TREND"
      ? data.rows.map((row) => ({
          period: String(row.period),
          loans: Number(row.loans_issued),
          returns: Number(row.returns_received),
        }))
      : [];
  const peak = Math.max(1, ...trend.map((row) => Math.max(row.loans, row.returns)));
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
          { label: "Sách tồn kho", value: String(data.metrics.copies_in_stock ?? 0) },
          { label: "Đang được mượn", value: String(data.metrics.copies_on_loan ?? 0) },
          { label: "Sách quá hạn", value: String(data.metrics.overdue_items ?? 0) },
          { label: "Tổng tiền phạt", value: formatVnd(data.metrics.fines_assessed ?? "0") },
        ]}
      />
      {trend.length > 0 && (
        <Panel title="Biểu đồ lượt mượn theo thời gian">
          <ul className="trend-chart" aria-label="Biểu đồ lượt mượn và lượt trả">
            {trend.map((row) => (
              <li key={row.period}>
                <span className="trend-label">{row.period}</span>
                <span
                  className="trend-bar trend-loans"
                  style={{ width: `${(row.loans / peak) * 100}%` }}
                  title={`Mượn: ${row.loans}`}
                />
                <span
                  className="trend-bar trend-returns"
                  style={{ width: `${(row.returns / peak) * 100}%` }}
                  title={`Trả: ${row.returns}`}
                />
                <span className="muted">
                  {row.loans} mượn · {row.returns} trả
                </span>
              </li>
            ))}
          </ul>
        </Panel>
      )}
      <Panel title="Chi tiết">
        {data.rows.length === 0 && data.report_type === "OVERVIEW" ? (
          <p className="muted">Báo cáo tổng quan chỉ gồm các chỉ số ở trên.</p>
        ) : (
          <Table
            caption="Chi tiết báo cáo"
            headers={columns.map((column) => COLUMN_LABELS[column] ?? column)}
            rows={data.rows.map((row) => columns.map((column) => shown(column, row[column])))}
          />
        )}
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
  // QĐ26: an export with no matching data has no file; ask before offering it.
  const link = useQuery({
    queryKey: ["reports", "download", jobId],
    enabled: !!jobId && job.data?.status === "SUCCEEDED",
    queryFn: async ({ signal }) =>
      (
        await services.reports.get_export_jobs_id_download({
          params: { path: { id: jobId! } },
          signal,
        })
      ).data!,
    retry: false,
  });
  const noData = link.error instanceof ApiError && link.error.code === "NO_DATA";
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
              {job.data.status === "SUCCEEDED" && noData && (
                <Notice tone="warning">
                  Không có dữ liệu phù hợp để xuất; hệ thống không tạo tệp (QĐ26).
                </Notice>
              )}
              {job.data.status === "SUCCEEDED" && !noData && (
                <div className="actions">
                  <Button
                    icon="download"
                    disabled={download.isPending || link.isPending}
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
