import { ApiError } from "../../api/errors";
import { Button, Notice, Panel } from "../../ui/components";
import type { ReactNode } from "react";

export function LoadingSkeleton({ books = false }: { books?: boolean }) {
  return (
    <div aria-busy="true" role="status" aria-label="Đang tải dữ liệu">
      <span className="sr-only">Đang tải dữ liệu…</span>
      {books ? (
        <div className="loading-grid">
          {Array.from({ length: 4 }, (_, i) => (
            <div key={i}>
              <span className="skeleton skeleton-cover" />
              <span className="skeleton skeleton-line" />
              <span className="skeleton skeleton-line" style={{ width: "60%" }} />
            </div>
          ))}
        </div>
      ) : (
        <Panel>
          {Array.from({ length: 5 }, (_, i) => (
            <span
              className="skeleton skeleton-line"
              key={i}
              style={{ maxWidth: "100%", height: 36, margin: "12px 0" }}
            />
          ))}
        </Panel>
      )}
    </div>
  );
}
export function ApiFailure({ error, retry }: { error: unknown; retry?: () => void }) {
  const apiError = error instanceof ApiError ? error : undefined;
  return (
    <Panel>
      <div className="error-panel">
        <h2>{apiError?.status === 404 ? "Không tìm thấy dữ liệu" : "Chưa thể tải dữ liệu"}</h2>
        <p className="muted">
          {apiError?.message ?? "Không thể kết nối với thư viện. Vui lòng thử lại."}
        </p>
        {apiError?.requestId && (
          <small className="request-id muted">Mã hỗ trợ: {apiError.requestId}</small>
        )}
        {retry && (
          <Button variant="secondary" icon="refresh" onClick={retry}>
            Thử lại
          </Button>
        )}
      </div>
    </Panel>
  );
}
export function MutationFeedback({
  error,
  success,
  children,
}: {
  error?: unknown;
  success?: boolean;
  children?: ReactNode;
}) {
  if (error)
    return (
      <Notice tone="danger">
        {error instanceof Error ? error.message : "Không thể lưu. Nội dung đang nhập được giữ lại."}
      </Notice>
    );
  return success ? <Notice>{children ?? "Hệ thống đã xác nhận thao tác."}</Notice> : null;
}
