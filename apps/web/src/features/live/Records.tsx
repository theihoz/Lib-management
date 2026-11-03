import { useInfiniteQuery } from "@tanstack/react-query";
import { useServices } from "../../auth/session";
import { formatDateTime } from "../../lib/datetime";
import { Button, Panel, Table } from "../../ui/components";
import type { ScreenDefinition } from "../types";
import { ApiFailure, LoadingSkeleton } from "./common";

/** F19: open loan items past their due time, computed by the server at query time. */
function OverdueList({ screen }: { screen: ScreenDefinition }) {
  const services = useServices();
  const result = useInfiniteQuery({
    queryKey: ["overdue"],
    initialPageParam: undefined as string | undefined,
    staleTime: 0,
    queryFn: async ({ pageParam, signal }) =>
      (
        await services.reports.get_overdue_items({
          params: { query: { cursor: pageParam, limit: 20 } },
          signal,
        })
      ).data!,
    getNextPageParam: (page) => page.nextCursor ?? undefined,
  });
  if (result.isPending) return <LoadingSkeleton />;
  if (result.error) return <ApiFailure error={result.error} retry={() => void result.refetch()} />;
  const items = result.data.pages.flatMap((page) => page.data);
  return (
    <Panel title={screen.title}>
      <Table
        caption={screen.title}
        headers={["Độc giả", "Sách", "Mã vạch", "Phiếu", "Hạn trả", "Quá hạn (ngày)"]}
        rows={items.map((row) => [
          `${row.reader.full_name} (${row.reader.reader_code})`,
          row.title,
          row.copy.barcode,
          row.loan.loan_no,
          formatDateTime(row.loanItem.due_at),
          String(row.lateDays),
        ])}
      />
      {result.hasNextPage && (
        <Button
          variant="secondary"
          disabled={result.isFetchingNextPage}
          onClick={() => void result.fetchNextPage()}
        >
          Tải thêm 20 mục
        </Button>
      )}
    </Panel>
  );
}

export default function Records({ screen }: { screen: ScreenDefinition }) {
  return <OverdueList screen={screen} />;
}
