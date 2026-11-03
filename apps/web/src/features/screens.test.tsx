import { render, screen, cleanup } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { screens } from "../app/screens";
import { FeatureView } from "./FeatureView";
import { fixtureFor } from "../dev/fixtures";

describe("Figma screen coverage", () => {
  it("renders all 71 screens as accessible React interfaces", () => {
    expect(screens).toHaveLength(71);
    expect(new Set(screens.map((item) => item.id)).size).toBe(71);
    expect(new Set(screens.map((item) => item.path)).size).toBe(71);
    for (const definition of screens) {
      render(<FeatureView screen={definition} preview sample={fixtureFor(definition.id)} />);
      expect(screen.getByRole("region", { name: definition.title })).toBeInTheDocument();
      cleanup();
    }
  });
  it("filters a reader list without modifying the fixture", async () => {
    const definition = screens.find((item) => item.id === "FE03.01")!;
    render(<FeatureView screen={definition} preview sample={fixtureFor(definition.id)} />);
    await userEvent.type(screen.getByRole("searchbox"), "Hà Linh");
    expect(screen.getByRole("table")).toHaveTextContent("Trần Hà Linh");
    expect(screen.getByRole("table")).not.toHaveTextContent("Nguyễn Minh An");
  });
  it("never submits a preview form as a real transaction", async () => {
    const definition = screens.find((item) => item.id === "FE03.03")!;
    render(<FeatureView screen={definition} preview sample={fixtureFor(definition.id)} />);
    await userEvent.click(screen.getByRole("button", { name: "Lưu hồ sơ" }));
    expect(await screen.findByRole("dialog")).toHaveTextContent("không ghi dữ liệu");
    expect(screen.queryByText("Đã lưu thành công")).not.toBeInTheDocument();
  });
  it("keeps unavailable mutations disabled in a live screen", () => {
    const definition = screens.find((item) => item.id === "FE03.03")!;
    render(<FeatureView screen={definition} />);
    expect(screen.getByRole("button", { name: "Lưu hồ sơ" })).toBeDisabled();
    expect(screen.queryByDisplayValue("Nguyễn Minh An")).not.toBeInTheDocument();
  });
});
