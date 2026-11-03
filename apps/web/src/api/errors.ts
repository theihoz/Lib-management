export class ApiError extends Error {
  constructor(public status: number, public code: string, message: string, public requestId?: string, public details: unknown[] = []) {
    super(message);
    this.name = "ApiError";
  }
}

export function toFieldErrors(details: unknown[]): Record<string, string> {
  const fields: Record<string, string> = {};
  for (const detail of details) {
    if (!detail || typeof detail !== "object" || !("loc" in detail) || !("msg" in detail) || !Array.isArray(detail.loc)) continue;
    const name: unknown = detail.loc.at(-1);
    if (typeof name === "string" && !["__proto__", "constructor", "prototype"].includes(name) && typeof detail.msg === "string") fields[name] = detail.msg;
  }
  return fields;
}

export async function responseError(response: Response): Promise<ApiError> {
  const body: unknown = await response.clone().json().catch(() => null);
  const value = body && typeof body === "object" ? body as Record<string, unknown> : {};
  return new ApiError(response.status, typeof value.code === "string" ? value.code : "INTERNAL_ERROR", typeof value.message === "string" ? value.message : "Không thể tải dữ liệu. Vui lòng thử lại.", typeof value.request_id === "string" ? value.request_id : response.headers.get("X-Request-ID") ?? undefined, Array.isArray(value.details) ? value.details : []);
}
