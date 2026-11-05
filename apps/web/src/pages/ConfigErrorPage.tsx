type Props = {
  reason: string;
  issues: string[];
};

/** Shown before auth/API start when /config.json is missing or invalid. */
export function ConfigErrorPage({ reason, issues }: Props) {
  return (
    <main className="standalone">
      <h1>Không khởi động được ứng dụng</h1>
      <div role="alert">
        <p>{reason}</p>
        {issues.length > 0 && (
          <ul aria-label="Chi tiết lỗi cấu hình">
            {issues.map((issue) => (
              <li key={issue}>{issue}</li>
            ))}
          </ul>
        )}
      </div>
      <p>Liên hệ quản trị viên vận hành để kiểm tra tệp config.json của môi trường này.</p>
    </main>
  );
}
