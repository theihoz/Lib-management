import { z } from "zod";

const httpUrl = z.url({ protocol: /^https?$/, error: "Phải là URL http(s) hợp lệ" });

/** Public runtime settings served as /config.json; never holds secrets. */
export const RuntimeConfigSchema = z
  .strictObject({
    /** Empty only for the demo build (mock: true), which has no identity provider. */
    oidcUrl: z.union([z.literal(""), httpUrl]),
    oidcRealm: z.string().min(1),
    oidcClientId: z.string().min(1),
    /** Empty string means same origin as the app. */
    apiBaseUrl: z.union([z.literal(""), httpUrl]),
    mock: z.boolean(),
  })
  .refine((c) => c.oidcUrl !== "" || (c.mock && import.meta.env.MODE !== "production"), {
    path: ["oidcUrl"],
    error: "Phải là URL http(s) hợp lệ",
  });

export type RuntimeConfig = z.infer<typeof RuntimeConfigSchema>;

export type ConfigResult =
  { ok: true; config: RuntimeConfig } | { ok: false; reason: string; issues: string[] };

export const CONFIG_PATH = `${import.meta.env.BASE_URL}config.json`;

export async function loadConfig(fetchFn: typeof fetch = fetch): Promise<ConfigResult> {
  let response: Response;
  try {
    response = await fetchFn(CONFIG_PATH, { cache: "no-store" });
  } catch {
    return { ok: false, reason: "Không tải được tệp cấu hình.", issues: [] };
  }
  if (!response.ok) {
    return {
      ok: false,
      reason: `Không tải được tệp cấu hình (HTTP ${response.status}).`,
      issues: [],
    };
  }

  let body: unknown;
  try {
    body = await response.json();
  } catch {
    return { ok: false, reason: "Tệp cấu hình không phải JSON hợp lệ.", issues: [] };
  }

  const parsed = RuntimeConfigSchema.safeParse(body);
  if (!parsed.success) {
    return {
      ok: false,
      reason: "Tệp cấu hình thiếu hoặc sai trường.",
      issues: parsed.error.issues.map((issue) => {
        const path = issue.path.join(".");
        return path ? `${path}: ${issue.message}` : issue.message;
      }),
    };
  }
  return { ok: true, config: parsed.data };
}
