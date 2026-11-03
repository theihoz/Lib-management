import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

// API runs on :8000 in the Dev Container; proxying keeps the app same-origin
// so the backend needs no CORS. Port 5173 is fixed: the Keycloak dev realm
// only allows redirects to http://localhost:5173/*.
const apiTarget = process.env.API_PROXY_TARGET ?? "http://localhost:8000";

export default defineConfig({
  // GitHub Pages serves under /<repo>/; CI sets VITE_BASE. Local/container builds use "/".
  base: process.env.VITE_BASE ?? "/",
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 5173,
    strictPort: true,
    proxy: {
      "/api": apiTarget,
      "/health": apiTarget,
      "/openapi.json": apiTarget,
    },
  },
  preview: {
    port: 4173,
    strictPort: true,
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test/setup.ts"],
    restoreMocks: true,
  },
});
