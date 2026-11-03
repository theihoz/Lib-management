// In-browser fake of the API, driven by the OpenAPI contract. Responses are generated
// from each operation's schema with a seeded RNG, so a reload shows the same data;
// collections keep created/edited rows in memory for the life of the tab.
import { findPersona } from "./personas";

type Schema = {
  $ref?: string;
  type?: string | string[];
  properties?: Record<string, Schema>;
  items?: Schema;
  required?: string[];
  enum?: unknown[];
  const?: unknown;
  format?: string;
  pattern?: string;
  minimum?: number;
  maximum?: number;
  maxLength?: number;
  allOf?: Schema[];
  anyOf?: Schema[];
  oneOf?: Schema[];
  "x-db-constraint"?: string;
};
type Operation = {
  parameters?: { name: string; in: string }[];
  requestBody?: unknown;
  responses?: Record<string, { content?: Record<string, { schema?: Schema }> }>;
  security?: unknown[];
  "x-permission"?: string;
};
export type OpenApi = {
  paths: Record<string, Record<string, Operation>>;
  components: { schemas: Record<string, Schema> };
};
type Row = Record<string, unknown>;

const TITLES = [
  "Dế Mèn phiêu lưu ký",
  "Số đỏ",
  "Tắt đèn",
  "Truyện Kiều",
  "Tôi thấy hoa vàng trên cỏ xanh",
  "Cánh đồng bất tận",
  "Nỗi buồn chiến tranh",
  "Chí Phèo",
  "Vợ nhặt",
  "Lão Hạc",
  "Mắt biếc",
  "Đất rừng phương Nam",
  "Nhập môn Công nghệ phần mềm",
  "Cấu trúc dữ liệu và giải thuật",
  "Cơ sở dữ liệu",
  "Lập trình Python căn bản",
];
const AUTHORS = [
  "Tô Hoài",
  "Vũ Trọng Phụng",
  "Ngô Tất Tố",
  "Nguyễn Du",
  "Nguyễn Nhật Ánh",
  "Nguyễn Ngọc Tư",
  "Bảo Ninh",
  "Nam Cao",
  "Kim Lân",
  "Đoàn Giỏi",
];
const PEOPLE = [
  "Nguyễn Minh An",
  "Trần Thu Hà",
  "Lê Quốc Bảo",
  "Phạm Gia Huy",
  "Võ Thanh Tâm",
  "Đặng Ngọc Lan",
  "Bùi Đức Long",
  "Hoàng Mai Anh",
  "Đỗ Khánh Linh",
  "Huỳnh Tấn Phát",
];
const CATEGORIES = ["Văn học", "Thiếu nhi", "Khoa học", "Công nghệ", "Lịch sử", "Kinh tế"];
const PUBLISHERS = ["NXB Kim Đồng", "NXB Trẻ", "NXB Văn học", "NXB Giáo dục", "NXB Hội Nhà văn"];
const LOCATIONS = ["Kho A · Kệ 1", "Kho A · Kệ 2", "Kho B · Kệ 4", "Phòng đọc tầng 2"];
const SENTENCES = [
  "Ấn bản được nhiều độc giả mượn trong học kỳ này.",
  "Ghi chú do thủ thư nhập khi tiếp nhận.",
  "Bản in rõ, bìa còn tốt.",
  "Tác phẩm kinh điển của văn học Việt Nam.",
];

function hash(text: string) {
  let h = 2166136261;
  for (let i = 0; i < text.length; i++) h = Math.imul(h ^ text.charCodeAt(i), 16777619);
  return h >>> 0;
}
function rngFrom(seed: string) {
  let state = hash(seed) || 1;
  return () => {
    state ^= state << 13;
    state ^= state >>> 17;
    state ^= state << 5;
    return (state >>> 0) / 4294967296;
  };
}
type Rng = () => number;
const pick = <T>(rng: Rng, list: readonly T[]) => list[Math.floor(rng() * list.length)]!;
const int = (rng: Rng, min: number, max: number) => min + Math.floor(rng() * (max - min + 1));
function uuid(rng: Rng) {
  const hex = Array.from({ length: 32 }, () => Math.floor(rng() * 16).toString(16));
  hex[12] = "4";
  hex[16] = "89ab"[Math.floor(rng() * 4)]!;
  const s = hex.join("");
  return `${s.slice(0, 8)}-${s.slice(8, 12)}-${s.slice(12, 16)}-${s.slice(16, 20)}-${s.slice(20)}`;
}
const DAY = 86_400_000;

export function createMockServer(spec: OpenApi, latencyMs = 150) {
  const store = new Map<string, Row[]>();
  const routes = Object.entries(spec.paths).map(([template, ops]) => {
    const names: string[] = [];
    const source = template.replace(/\{(\w+)\}/g, (_, name: string) => {
      names.push(name);
      return "([^/]+)";
    });
    return { template, ops, names, regex: new RegExp(`^${source}$`) };
  });

  const resolve = (schema: Schema): Schema => {
    if (!schema.$ref) return schema;
    const name = schema.$ref.split("/").at(-1)!;
    return resolve(spec.components.schemas[name] ?? {});
  };

  function text(name: string, context: string, schema: Schema, rng: Rng): string {
    const key = name.toLowerCase();
    const ctx = context.toLowerCase();
    const choices = schema["x-db-constraint"]?.match(/^[A-Z_]+(\/[A-Z_]+)+$/);
    if (choices) return pick(rng, choices[0].split("/"));
    if (schema.format === "uuid" || key === "id" || key.endsWith("_id") || name.endsWith("Id"))
      return uuid(rng);
    if (schema.format === "date-time") return isoAt(key, rng);
    if (schema.format === "date")
      return key.includes("birth")
        ? `${int(rng, 1970, 2008)}-0${int(rng, 1, 9)}-1${int(rng, 0, 9)}`
        : isoAt(key, rng).slice(0, 10);
    if (schema.format === "email" || key.includes("email"))
      return `docgia${int(rng, 1, 999)}@thuvien.example`;
    if (schema.format === "uri") return "https://example.org/demo";
    if (schema.pattern === "^[0-9]+$")
      return String(int(rng, 1, 40) * (key.includes("rate") ? 1000 : 5000));
    if (schema.pattern?.startsWith("^[0-9a-f]{64}"))
      return Array.from({ length: 64 }, () => Math.floor(rng() * 16).toString(16)).join("");
    if (key === "isbn") return `978604${int(rng, 1000000, 9999999)}`;
    if (key === "language") return "vi";
    if (key === "title") return pick(rng, TITLES);
    if (key.includes("phone")) return `09${int(rng, 10000000, 99999999)}`;
    if (key === "address") return `${int(rng, 1, 300)} Lê Lợi, Quận 1, TP.HCM`;
    if (key.includes("barcode")) return `BC${int(rng, 100000, 999999)}`;
    if (key.endsWith("_no") || key.endsWith("no") || key.endsWith("code"))
      return `${(key.split("_")[0] ?? "x").slice(0, 3).toUpperCase()}-${int(rng, 1000, 9999)}`;
    if (key.includes("name") || key === "label") {
      if (ctx.includes("author")) return pick(rng, AUTHORS);
      if (ctx.includes("categor")) return pick(rng, CATEGORIES);
      if (ctx.includes("publisher")) return pick(rng, PUBLISHERS);
      if (ctx.includes("location")) return pick(rng, LOCATIONS);
      if (ctx.includes("role")) return pick(rng, ["Thủ thư", "Quản lý", "Độc giả"]);
      return pick(rng, PEOPLE);
    }
    if (key.includes("type")) return pick(rng, ["X", "Y", "Z"]);
    if (key.includes("status") || key.includes("state")) return "ACTIVE";
    const value = pick(rng, SENTENCES);
    return schema.maxLength && value.length > schema.maxLength
      ? value.slice(0, schema.maxLength)
      : value;
  }

  function isoAt(key: string, rng: Rng) {
    const future = /due|expire|until|valid_to|deadline|hold/.test(key);
    const offset = int(rng, 1, 40) * DAY + int(rng, 0, 8) * 3_600_000;
    return new Date(Date.now() + (future ? offset : -offset)).toISOString();
  }

  function generate(schema: Schema, name: string, context: string, rng: Rng, depth = 0): unknown {
    const s = resolve(schema);
    if (s.const !== undefined) return s.const;
    if (s.enum?.length) return pick(rng, s.enum);
    if (s.allOf) {
      const parts = s.allOf.map((part) => generate(part, name, context, rng, depth));
      return parts.every((p) => p && typeof p === "object")
        ? Object.assign({}, ...(parts as Row[]))
        : parts.at(-1);
    }
    const variants = s.anyOf ?? s.oneOf;
    if (variants) {
      const real = variants.filter((v) => resolve(v).type !== "null");
      return real.length ? generate(pick(rng, real), name, context, rng, depth) : null;
    }
    const types = Array.isArray(s.type) ? s.type : [s.type];
    const type = types.find((t) => t && t !== "null") ?? (s.properties ? "object" : undefined);
    const key = name.toLowerCase();
    switch (type) {
      case "object": {
        const out: Row = {};
        for (const [prop, child] of Object.entries(s.properties ?? {}))
          if (depth < 5) out[prop] = generate(child, prop, `${context}.${name}`, rng, depth + 1);
        return out;
      }
      case "array":
        if (depth >= 5 || !s.items) return [];
        return Array.from({ length: int(rng, 1, 3) }, () =>
          generate(s.items!, name, `${context}.${name}`, rng, depth + 1),
        );
      case "integer":
      case "number": {
        if (key.includes("year")) return int(rng, 1990, 2025);
        if (key === "version") return 1;
        const min = s.minimum ?? 0;
        return int(rng, min, Math.min(s.maximum ?? min + 9, min + 9));
      }
      case "boolean":
        return rng() < 0.7;
      case "string":
        return text(name, context, s, rng);
      default:
        return null;
    }
  }

  const successSchema = (op: Operation) => {
    const [code, response] =
      Object.entries(op.responses ?? {}).find(([status]) => status.startsWith("2")) ?? [];
    return {
      status: Number(code ?? 200),
      schema: response?.content?.["application/json"]?.schema,
      csv: Boolean(response && !response.content?.["application/json"]),
    };
  };
  const listItems = (schema: Schema | undefined) => {
    const s = schema && resolve(schema);
    const data = s?.properties?.data;
    return data && resolve(data).type === "array" ? resolve(data).items : undefined;
  };

  function collection(path: string, op: Operation) {
    let rows = store.get(path);
    if (!rows) {
      const items = listItems(successSchema(op).schema);
      const rng = rngFrom(path);
      rows = items
        ? Array.from({ length: 12 }, (_, i) => {
            const row = generate(items, path, path, rng) as Row;
            if (typeof row.title === "string") row.title = TITLES[i % TITLES.length];
            return row;
          })
        : [];
      store.set(path, rows);
    }
    return rows;
  }
  // Values the caller asked for (path ids, barcode, cardNo…) show up in the answer.
  function overlay(target: unknown, values: Row, depth = 0) {
    if (!target || typeof target !== "object" || depth > 2) return;
    for (const [key, value] of Object.entries(target as Row)) {
      if (key in values && typeof value === typeof values[key]) (target as Row)[key] = values[key];
      else overlay(value, values, depth + 1);
    }
  }

  const json = (status: number, body: unknown) =>
    new Response(status === 204 ? null : JSON.stringify(body), {
      status,
      headers: { "Content-Type": "application/json", "X-Request-ID": crypto.randomUUID() },
    });
  const error = (status: number, code: string, message: string) =>
    json(status, { code, message, request_id: crypto.randomUUID(), details: [] });

  async function handle(request: Request): Promise<Response> {
    const url = new URL(request.url);
    const method = request.method.toLowerCase();
    if (latencyMs) await new Promise((r) => setTimeout(r, latencyMs * (0.5 + Math.random())));

    let route: (typeof routes)[number] | undefined;
    let params: Record<string, string> = {};
    for (const candidate of routes) {
      const match = candidate.regex.exec(url.pathname);
      if (match && candidate.ops[method]) {
        route = candidate;
        params = Object.fromEntries(
          candidate.names.map((n, i) => [n, decodeURIComponent(match[i + 1]!)]),
        );
        break;
      }
    }
    if (!route) return error(404, "NOT_FOUND", "Không tìm thấy tài nguyên.");
    const op = route.ops[method]!;

    const token = request.headers.get("Authorization")?.replace(/^Bearer mock-/, "");
    const persona = findPersona(token);
    const permission = op["x-permission"];
    const isPublic = Array.isArray(op.security) && op.security.length === 0;
    if (url.pathname === "/api/v1/auth/me") {
      if (!persona) return error(401, "INVALID_TOKEN", "Phiên đăng nhập đã hết hạn.");
      if (persona.failure)
        return error(403, persona.failure, "Tài khoản không thể dùng hệ thống lúc này.");
      return json(200, {
        account: {
          id: uuid(rngFrom(persona.code)),
          reader_id: persona.code === "READER" ? uuid(rngFrom("reader")) : null,
          display_name: persona.displayName,
          status: "ACTIVE",
        },
        permissions: persona.permissions,
      });
    }
    if (url.pathname.startsWith("/health/")) return json(200, { status: "ready" });
    if (permission && !isPublic) {
      if (!persona) return error(401, "INVALID_TOKEN", "Phiên đăng nhập đã hết hạn.");
      if (!persona.permissions.includes(permission))
        return error(403, "PERMISSION_DENIED", "Bạn không có quyền thực hiện thao tác này.");
    }

    const { status, schema, csv } = successSchema(op);
    if (csv)
      return new Response("ma,ten,so_luong\nBC100001,Dế Mèn phiêu lưu ký,3\n", {
        status,
        headers: { "Content-Type": "text/csv" },
      });
    const query = Object.fromEntries(url.searchParams) as Row;
    const body: Row =
      method === "get" ? {} : (((await request.json().catch(() => ({}))) as Row) ?? {});
    const parent = route.template.replace(/\/\{\w+\}$/, "");
    const parentOps = spec.paths[parent];
    const concrete = url.pathname.replace(/\/[^/]+$/, "");

    if (method === "get" && listItems(schema)) {
      let rows = collection(url.pathname, op);
      const search = typeof query.query === "string" ? query.query.toLowerCase() : "";
      if (search) rows = rows.filter((r) => JSON.stringify(r).toLowerCase().includes(search));
      const limit = Number(query.limit) || 20;
      return json(status, { data: rows.slice(0, limit), nextCursor: null });
    }

    const rng = rngFrom(`${method} ${url.pathname} ${url.search}`);
    const result = schema ? generate(schema, route.template, route.template, rng) : null;
    overlay(result, { ...query, ...params });
    const listOp = route.template.endsWith("}") ? parentOps?.get : undefined;
    const rows = listOp ? collection(concrete, listOp) : undefined;
    const existing = rows?.find((r) => r.id === params.id);

    if (method === "get") {
      if (existing && result && typeof result === "object") Object.assign(result, existing);
      return json(status, result);
    }
    if (result && typeof result === "object") {
      const row = result as Row;
      for (const key of Object.keys(body)) if (key in row) row[key] = body[key];
      if (existing) {
        Object.assign(existing, body, { version: Number(existing.version ?? 1) + 1 });
        Object.assign(row, existing);
      } else if (method === "post" && spec.paths[route.template]?.get) {
        // POST to a collection: new row appears at the top of the list.
        collection(url.pathname, spec.paths[route.template]!.get!).unshift(row);
      }
    }
    return json(status, result);
  }

  return { handle };
}
