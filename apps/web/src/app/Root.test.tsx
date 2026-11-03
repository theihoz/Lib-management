import { render, screen } from "@testing-library/react";
import { Root } from "./Root";

describe("Root", () => {
  beforeEach(() => {
    window.history.replaceState(null, "", "/catalog");
    vi.stubGlobal("fetch", (input: string | Request) => {
      const url = typeof input === "string" ? input : input.url;
      return Promise.resolve(
        Response.json(
          url.includes("/health/") ? { status: "ready" } : { data: [], nextCursor: null },
        ),
      );
    });
  });
  afterEach(() => {
    vi.unstubAllGlobals();
  });
  it("shows the config error page with each issue when config is invalid", () => {
    render(
      <Root
        result={{
          ok: false,
          reason: "Tệp cấu hình thiếu hoặc sai trường.",
          issues: ["oidcUrl: x"],
        }}
      />,
    );
    expect(
      screen.getByRole("heading", { name: "Không khởi động được ứng dụng" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("alert")).toHaveTextContent("Tệp cấu hình thiếu hoặc sai trường.");
    expect(screen.getByRole("listitem")).toHaveTextContent("oidcUrl: x");
  });

  it("renders the app when config is valid", () => {
    render(
      <Root
        result={{
          ok: true,
          config: {
            oidcUrl: "http://localhost:8080",
            oidcRealm: "lib-management",
            oidcClientId: "lib-management-web",
            apiBaseUrl: "",
            mock: false,
          },
        }}
      />,
    );
    expect(screen.getByRole("heading", { name: "Khám phá sách", level: 1 })).toBeInTheDocument();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });
});
