import createClient from "openapi-fetch";
import type { paths } from "./schema";
import { ApiError, responseError } from "./errors";

export type ClientOptions = {
  baseUrl?: string;
  getToken?: () => Promise<string | undefined>;
  refresh?: () => Promise<boolean>;
  onExpired?: () => void;
  onForbidden?: () => void;
  fetch?: (request: Request) => Promise<Response>;
};

export function createApiClient(options: ClientOptions = {}) {
  const send = options.fetch ?? ((request: Request) => fetch(request));
  return createClient<paths>({
    baseUrl:
      options.baseUrl ||
      (typeof window === "undefined" ? "http://localhost" : window.location.origin),
    fetch: async (original: Request) => {
      const request = original.clone();
      request.headers.set("X-Request-ID", crypto.randomUUID());
      let response: Response;
      try {
        const token = await options.getToken?.();
        if (token) request.headers.set("Authorization", `Bearer ${token}`);
        // Keep an unconsumed clone: a POST body can be read only once.
        const retry = request.clone();
        response = await send(request);
        if (response.status === 401 && options.refresh && (await options.refresh())) {
          const freshToken = await options.getToken?.();
          if (freshToken) retry.headers.set("Authorization", `Bearer ${freshToken}`);
          response = await send(retry);
        }
      } catch (error) {
        if (error instanceof DOMException && error.name === "AbortError") throw error;
        if (error instanceof ApiError) {
          if (error.status === 401) options.onExpired?.();
          throw error;
        }
        throw new ApiError(0, "NETWORK_ERROR", "Không thể kết nối. Kiểm tra mạng rồi thử lại.");
      }
      if (response.status === 401) options.onExpired?.();
      if (!response.ok) {
        const error = await responseError(response);
        if (response.status === 403 && error.code === "PERMISSION_DENIED") options.onForbidden?.();
        throw error;
      }
      return response;
    },
  });
}

export type ApiClient = ReturnType<typeof createApiClient>;
