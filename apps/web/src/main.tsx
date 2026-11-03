import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { Root } from "./app/Root";
import { loadConfig } from "./config/config";
import type { DemoMode } from "./auth/session";

const container = document.getElementById("root");
if (!container) throw new Error("Missing #root element");

const result = await loadConfig();
let demo: DemoMode | undefined;
// Rollup drops this branch, and the whole mock chunk, from production builds.
if (import.meta.env.MODE !== "production" && result.ok && result.config.mock) {
  demo = (await import("./mock")).createDemoMode();
}
createRoot(container).render(
  <StrictMode>
    <Root result={result} demo={demo} />
  </StrictMode>,
);
