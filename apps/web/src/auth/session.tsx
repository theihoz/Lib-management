import { createContext, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import type { RuntimeConfig } from "../config/config";
import type { components } from "../api/schema";
import { createApiClient } from "../api/client";
import { createServices } from "../api/services";
import type { ApiServices } from "../api/services";
import { createIdentity } from "./keycloak";
import type { Identity } from "./keycloak";
import { classifySessionError } from "./session-state";
import type { SessionStatus } from "./session-state";

/** Demo build only: fake API and persona sign-in in place of the API and Keycloak. */
export type DemoMode = {
  createIdentity: () => Identity;
  fetch: (request: Request) => Promise<Response>;
  personas: { code: string; label: string }[];
};

type Session = {
  status: SessionStatus;
  /** False until the identity provider's silent check has settled. */
  initialized: boolean;
  account?: components["schemas"]["AccountView"];
  permissions: string[];
  /** Present in the demo build; login() then takes one of these codes. */
  personas?: DemoMode["personas"];
  login: (persona?: string) => Promise<void>;
  logout: () => Promise<void>;
  retry: () => void;
  services: ApiServices;
  error?: unknown;
};
const SessionContext = createContext<Session | null>(null);
export function SessionProvider({
  config,
  demo,
  children,
}: {
  config: RuntimeConfig;
  demo?: DemoMode;
  children: ReactNode;
}) {
  const cache = useQueryClient();
  const identity = useMemo(
    () => (demo ? demo.createIdentity() : createIdentity(config)),
    [config, demo],
  );
  const isCallback = useMemo(() => {
    const params = new URLSearchParams(window.location.search);
    return params.has("state") && (params.has("code") || params.has("error"));
  }, []);
  const [phase, setPhase] = useState<SessionStatus>(isCallback ? "checking" : "anonymous");
  const [hasToken, setHasToken] = useState(false);
  const [initialized, setInitialized] = useState(false);
  const [loginError, setLoginError] = useState<unknown>();
  const services = useMemo(
    () =>
      createServices(
        createApiClient({
          baseUrl: config.apiBaseUrl,
          fetch: demo?.fetch,
          getToken: () => identity.getToken(),
          refresh: () => identity.refresh(),
          onExpired: () => {
            setPhase("expired");
            setHasToken(false);
            identity.clear();
            cache.clear();
          },
          onForbidden: () => {
            void cache.invalidateQueries({ queryKey: ["auth", "me"] });
          },
        }),
      ),
    [config.apiBaseUrl, demo, identity, cache],
  );
  const auth = useQuery({
    queryKey: ["auth", "me"],
    queryFn: async () => (await services.identity.get_auth_me({})).data!,
    enabled: hasToken,
    retry: false,
    staleTime: 0,
    refetchOnWindowFocus: true,
  });
  useEffect(() => {
    let active = true;
    void identity
      .init()
      .then((authenticated) => {
        if (active) {
          setHasToken(authenticated);
          setPhase(authenticated ? "checking" : "anonymous");
          setInitialized(true);
        }
      })
      .catch((error: unknown) => {
        if (!active) return;
        setInitialized(true);
        // Public pages keep working when the identity provider is unreachable.
        if (!isCallback) return setPhase("anonymous");
        setLoginError(error);
        setPhase("offline");
      });
    return () => {
      active = false;
    };
  }, [identity, isCallback]);
  const status: SessionStatus = hasToken
    ? auth.error
      ? classifySessionError(auth.error)
      : auth.data
        ? "authenticated"
        : "checking"
    : phase;
  const value: Session = {
    status,
    initialized,
    account: status === "authenticated" ? auth.data?.account : undefined,
    permissions: status === "authenticated" ? (auth.data?.permissions ?? []) : [],
    personas: demo?.personas,
    services,
    error: auth.error ?? loginError,
    async login(persona) {
      setLoginError(undefined);
      setPhase("checking");
      try {
        if (await identity.login(persona)) setHasToken(true);
      } catch (error) {
        setLoginError(error);
        setPhase("offline");
      }
    },
    async logout() {
      cache.clear();
      setHasToken(false);
      setPhase("anonymous");
      try {
        await identity.logout();
      } catch (error) {
        identity.clear();
        setLoginError(error);
        setPhase("offline");
      }
    },
    retry() {
      if (hasToken) void auth.refetch();
      else {
        setLoginError(undefined);
        setPhase("anonymous");
      }
    },
  };
  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}
export function useSession() {
  const value = useContext(SessionContext);
  if (!value) throw new Error("SessionProvider missing");
  return value;
}
export function useServices() {
  return useSession().services;
}
