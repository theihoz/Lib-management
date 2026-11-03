import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { Root } from "./app/Root";
import { loadConfig } from "./config/config";

const container = document.getElementById("root");
if (!container) throw new Error("Missing #root element");

const result = await loadConfig();
createRoot(container).render(
  <StrictMode>
    <Root result={result} />
  </StrictMode>,
);
