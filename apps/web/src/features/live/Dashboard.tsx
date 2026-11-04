import { useQuery } from "@tanstack/react-query";
import { Link, useNavigate } from "react-router";
import { useServices, useSession } from "../../auth/session";
import { formatDateTime } from "../../lib/datetime";
import { Panel, Stats, Table } from "../../ui/components";
import { ApiFailure, LoadingSkeleton } from "./common";

/** YC#19 / BM14: overdue books and the most borrowed books at a glance. */
export default function Dashboard() {
  const services = useServices();
  const session = useSession();
  const navigate = useNavigate();
  const board = useQuery({
    queryKey: ["dashboard"],
    queryFn: async ({ signal }) => (await services.reports.get_dashboard({ signal })).data!,
    refetchInterval: 60_000,
  });
  if (board.isPending) return <LoadingSkeleton />;
  if (board.error) return <ApiFailure error={board.error} retry={() => void board.refetch()} />;
  const data = board.data;
  return (
    <div className="stack">
      <Stats
        items={[
          { label: "Sách quá hạn", value: String(data.overdueCount) },
          { label: "Lượt mượn hôm nay", value: String(data.loansToday) },
          { label: "Lượt trả hôm nay", value: String(data.returnsToday) },
          { label: "Sách tồn kho", value: String(data.copiesInStock) },
          { label: "Đang được mượn", value: String(data.copiesOnLoan) },
        ]}
      />
      <Panel title="Sách quá hạn" subtitle="10 mục quá hạn lâu nhất">
        <Table
          caption="Sách quá hạn"
          headers={["Độc giả", "Họ tên", "Sách", "Mã vạch", "Hạn trả", "Số ngày trễ"]}
          rows={data.overdueTop.map((row) => [
            row.reader_code,
            row.full_name,
            row.title,
            row.barcode,
            formatDateTime(row.due_at),
            String(row.late_days),
          ])}
          onRow={(index) => {
            const row = data.overdueTop[index];
            if (row) void navigate(`/staff/readers/${row.reader_id}`);
          }}
          empty={{ title: "Không có sách quá hạn", hint: "Mọi khoản mượn đều còn trong hạn." }}
        />
        <Link to="/staff/overdue">Xem toàn bộ danh sách quá hạn</Link>
      </Panel>
      <Panel title="Sách được mượn nhiều nhất" subtitle="30 ngày gần nhất">
        <Table
          caption="Sách được mượn nhiều nhất"
          headers={["Sách", "Thể loại", "Lượt mượn"]}
          rows={data.topBooks30d.map((row) => [
            row.title,
            row.categories || "—",
            String(row.loan_count),
          ])}
          empty={{ title: "Chưa có lượt mượn", hint: "Chưa có sách nào được mượn trong 30 ngày." }}
        />
        {session.permissions.includes("report.read") && (
          <Link to="/manager/reports">Tạo báo cáo chi tiết (BM08)</Link>
        )}
      </Panel>
      <p className="muted">Cập nhật lúc {formatDateTime(data.asOf)}; tự làm mới mỗi phút.</p>
    </div>
  );
}
