import { loadSpec } from ".";
import { createMockServer } from "./server";

type Row = { id: string; name: string };
type Page = { data: Row[]; nextCursor: string | null };
type Failure = { code: string };

const server = createMockServer(loadSpec(), 0);
const call = (path: string, persona?: string, init: RequestInit = {}) =>
  server.handle(
    new Request(`http://localhost${path}`, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        ...(persona ? { Authorization: `Bearer mock-${persona}` } : {}),
      },
    }),
  );
const read = async <T>(response: Response | Promise<Response>) =>
  (await (await response).json()) as T;

describe("mock server", () => {
  it("answers /auth/me with the persona's permissions", async () => {
    const body = await read<{ account: { display_name: string }; permissions: string[] }>(
      call("/api/v1/auth/me", "LIBRARIAN"),
    );
    expect(body.account.display_name).toBe("Trần Thu Hà");
    expect(body.permissions).toContain("loan.checkout");
  });

  it("maps unlinked and inactive personas to their error codes", async () => {
    const response = await call("/api/v1/auth/me", "NOT_LINKED");
    expect(response.status).toBe(403);
    expect((await read<Failure>(response)).code).toBe("ACCOUNT_NOT_LINKED");
    expect((await read<Failure>(call("/api/v1/auth/me", "INACTIVE"))).code).toBe(
      "ACCOUNT_INACTIVE",
    );
  });

  it("serves the public catalog without a session and is stable across calls", async () => {
    const first = await read<Page>(call("/api/v1/book-editions?limit=5"));
    expect(first.data).toHaveLength(5);
    expect(first.nextCursor).toBeNull();
    expect(await read<Page>(call("/api/v1/book-editions?limit=5"))).toEqual(first);
  });

  it("enforces the operation permission", async () => {
    expect((await call("/api/v1/readers")).status).toBe(401);
    const denied = await call("/api/v1/readers", "SYSTEM_ADMIN");
    expect(denied.status).toBe(403);
    expect((await read<Failure>(denied)).code).toBe("PERMISSION_DENIED");
    expect((await call("/api/v1/readers", "LIBRARIAN")).status).toBe(200);
  });

  it("keeps created and edited rows for the life of the server", async () => {
    const created = await read<Row>(
      call("/api/v1/authors", "LIBRARIAN", {
        method: "POST",
        body: JSON.stringify({ name: "Xuân Quỳnh" }),
      }),
    );
    expect(created.name).toBe("Xuân Quỳnh");
    const list = await read<Page>(call("/api/v1/authors?query=xuân", "LIBRARIAN"));
    expect(list.data[0]?.id).toBe(created.id);

    await call(`/api/v1/authors/${created.id}`, "LIBRARIAN", {
      method: "PATCH",
      body: JSON.stringify({ name: "Xuân Quỳnh (sửa)" }),
    });
    const detail = await read<Row>(call(`/api/v1/authors/${created.id}`, "LIBRARIAN"));
    expect(detail.name).toBe("Xuân Quỳnh (sửa)");
  });

  it("echoes looked-up values into the answer", async () => {
    const body = await read<{ copy: { barcode: string } }>(
      call("/api/v1/copies/lookup?barcode=BC123456", "LIBRARIAN"),
    );
    expect(body.copy.barcode).toBe("BC123456");
  });
});
