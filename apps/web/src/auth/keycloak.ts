import type Keycloak from "keycloak-js";
import type { RuntimeConfig } from "../config/config";
import { ApiError } from "../api/errors";

/** Sign-in provider seen by the session; the demo build swaps in a persona picker. */
export type Identity = {
  init(): Promise<boolean>;
  /** Resolves true when signed in without leaving the page (demo personas). */
  login(persona?: string): Promise<boolean>;
  logout(): Promise<void>;
  getToken(): Promise<string | undefined>;
  refresh(): Promise<boolean>;
  clear(): void;
};

export function createIdentity(config: RuntimeConfig): Identity {
  let client: Keycloak | undefined;
  let loading: Promise<Keycloak> | undefined;
  const getClient = () =>
    (loading ??= import("keycloak-js").then(
      ({ default: Identity }) =>
        (client ??= new Identity({
          url: config.oidcUrl,
          realm: config.oidcRealm,
          clientId: config.oidcClientId,
        })),
    ));
  let initializing: Promise<boolean> | undefined;
  const init = () =>
    (initializing ??= getClient().then((identity) =>
      identity.init({
        onLoad: "check-sso",
        silentCheckSsoRedirectUri: `${window.location.origin}${import.meta.env.BASE_URL}silent-check-sso.html`,
        pkceMethod: "S256",
        checkLoginIframe: false,
        responseMode: "query",
        messageReceiveTimeout: 5000,
      }),
    ));
  return {
    init,
    async login() {
      await init();
      await (
        await getClient()
      ).login({ redirectUri: `${window.location.origin}${import.meta.env.BASE_URL}me` });
      return false;
    },
    async logout() {
      if (!client) return;
      await client.logout({
        redirectUri: `${window.location.origin}${import.meta.env.BASE_URL}catalog`,
      });
    },
    async getToken() {
      if (!client?.authenticated) return undefined;
      try {
        await client.updateToken(30);
      } catch {
        throw new ApiError(
          client.authenticated ? 0 : 401,
          client.authenticated ? "NETWORK_ERROR" : "INVALID_TOKEN",
          client.authenticated
            ? "Không thể làm mới phiên. Vui lòng thử lại."
            : "Phiên đăng nhập đã hết hạn.",
        );
      }
      return client.token;
    },
    async refresh() {
      if (!client?.authenticated) return false;
      try {
        await client.updateToken(-1);
        return true;
      } catch {
        await client.clearToken();
        return false;
      }
    },
    clear() {
      if (client) void client.clearToken();
    },
  };
}
