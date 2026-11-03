import type { RuntimeConfig } from "../config/config";

type Props = {
  config: RuntimeConfig;
};

/** Placeholder until shell/auth land (spec M0 frontend, PR 3–4). */
export function App({ config }: Props) {
  return (
    <main>
      <h1>Lib-management</h1>
      <p>Khung ứng dụng frontend đã khởi động.</p>
      {config.mock && <p>Đang chạy chế độ mock.</p>}
    </main>
  );
}
