import type { Identity } from "../auth/keycloak";
import type { DemoMode } from "../auth/session";
import { MOCK_MARKER, findPersona, personas } from "./personas";
import { createMockServer } from "./server";
import type { OpenApi } from "./server";

const PERSONA_KEY = "lib-demo-persona";
// Demo only: the persona code (never a token or PII) survives reloads and deep links in this tab.
const storage = () =>
  // eslint-disable-next-line no-restricted-globals -- persona code only, mock build only
  sessionStorage;
function remember(code: string | undefined) {
  try {
    if (code) storage().setItem(PERSONA_KEY, code);
    else storage().removeItem(PERSONA_KEY);
  } catch {
    // Storage blocked: the demo still works until the next reload.
  }
}
function recall() {
  try {
    return findPersona(storage().getItem(PERSONA_KEY) ?? undefined)?.code;
  } catch {
    return undefined;
  }
}

function createMockIdentity(): Identity {
  let current = recall();
  const set = (code: string | undefined) => {
    current = code;
    remember(code);
  };
  return {
    init: () => Promise.resolve(current !== undefined),
    login(persona) {
      set(findPersona(persona)?.code ?? "READER");
      return Promise.resolve(true);
    },
    logout() {
      set(undefined);
      return Promise.resolve();
    },
    getToken: () => Promise.resolve(current && `mock-${current}`),
    refresh: () => Promise.resolve(current !== undefined),
    clear() {
      set(undefined);
    },
  };
}

// Glob rather than a JSON import: Vite inlines the contract into the demo chunk, and
// tsc never needs the file (the web Docker image copies only apps/web).
const contracts = import.meta.glob<OpenApi>("../../../../docs/design/openapi.json", {
  eager: true,
  import: "default",
});
export function loadSpec(): OpenApi {
  const spec = Object.values(contracts)[0];
  if (!spec) throw new Error("docs/design/openapi.json missing from the demo build");
  return spec;
}

export function createDemoMode(): DemoMode {
  console.info(MOCK_MARKER, "API calls are answered inside the browser.");
  const server = createMockServer(loadSpec());
  return {
    createIdentity: createMockIdentity,
    fetch: (request) => server.handle(request),
    personas: personas.map(({ code, label }) => ({ code, label })),
  };
}
