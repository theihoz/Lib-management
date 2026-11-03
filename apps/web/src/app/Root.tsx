import type { ConfigResult } from "../config/config";
import { ConfigErrorPage } from "../pages/ConfigErrorPage";
import { App } from "./App";

export function Root({ result }: { result: ConfigResult }) {
  return result.ok ? (
    <App config={result.config} />
  ) : (
    <ConfigErrorPage reason={result.reason} issues={result.issues} />
  );
}
