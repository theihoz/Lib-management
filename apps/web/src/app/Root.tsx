import type { ConfigResult } from "../config/config";
import type { DemoMode } from "../auth/session";
import { ConfigErrorPage } from "../pages/ConfigErrorPage";
import { App } from "./App";

export function Root({ result, demo }: { result: ConfigResult; demo?: DemoMode }) {
  return result.ok ? (
    <App config={result.config} demo={demo} />
  ) : (
    <ConfigErrorPage reason={result.reason} issues={result.issues} />
  );
}
