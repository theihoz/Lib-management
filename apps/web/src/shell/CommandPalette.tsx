import { useEffect, useId, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router";
import { useServices, useSession } from "../auth/session";
import { isStaff } from "../auth/session-state";
import type { ScreenDefinition } from "../features/types";
import { useDebounced } from "../lib/useDebounced";
import { Button, Dialog } from "../ui/components";
import { isPaletteShortcut, matchScreens } from "./palette";

type Item = { key: string; group: string; label: string; detail?: string; to: string };

/** YC#18: Ctrl+K / ⌘K search across screens, books and (for staff) readers. */
export function CommandPalette({ screens }: { screens: ScreenDefinition[] }) {
  const services = useServices();
  const session = useSession();
  const navigate = useNavigate();
  const listId = useId();
  const [open, setOpen] = useState(false);
  const [text, setText] = useState("");
  const [active, setActive] = useState(0);
  const input = useRef<HTMLInputElement>(null);
  useEffect(() => {
    if (open) input.current?.focus();
  }, [open]);
  const keyword = useDebounced(text, 250).trim();
  const canReaders = session.permissions.includes("reader.read") && isStaff(session.permissions);
  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (!isPaletteShortcut(event)) return;
      event.preventDefault();
      setOpen(true);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);
  // QĐ23: a blank keyword never reaches the API.
  const books = useQuery({
    queryKey: ["palette", "books", keyword],
    enabled: open && keyword !== "",
    queryFn: async ({ signal }) =>
      (
        await services.catalog.get_book_editions({
          params: { query: { query: keyword, limit: 5 } },
          signal,
        })
      ).data!.data,
  });
  const readers = useQuery({
    queryKey: ["palette", "readers", keyword],
    enabled: open && keyword !== "" && canReaders,
    queryFn: async ({ signal }) =>
      (
        await services.readers.get_readers_lookup({
          params: { query: { query: keyword } },
          signal,
        })
      ).data!.data.slice(0, 5),
  });
  const items: Item[] = [
    ...matchScreens(text, screens).map((screen) => ({
      key: `screen-${screen.id}`,
      group: "Điều hướng",
      label: screen.title,
      to: screen.path,
    })),
    ...(books.data ?? []).map((book) => ({
      key: `book-${book.id}`,
      group: "Sách",
      label: book.title,
      detail: book.authors?.map((author) => author.name).join(", "),
      to: `/catalog/${book.id}`,
    })),
    ...(readers.data ?? []).map((reader) => ({
      key: `reader-${reader.id}`,
      group: "Độc giả",
      label: reader.full_name,
      detail: reader.reader_code,
      to: `/staff/readers/${reader.id}`,
    })),
  ];
  const close = () => {
    setOpen(false);
    setText("");
    setActive(0);
  };
  const go = (item: Item | undefined) => {
    if (!item) return;
    close();
    void navigate(item.to);
  };
  const searching = keyword !== "" && (books.isFetching || readers.isFetching);
  return (
    <>
      <Button
        variant="ghost"
        icon="search"
        aria-keyshortcuts="Control+K"
        onClick={() => setOpen(true)}
      >
        Tìm nhanh <kbd>Ctrl K</kbd>
      </Button>
      <Dialog open={open} title="Tìm kiếm nhanh" onClose={close}>
        <div className="command-palette">
          <input
            ref={input}
            role="combobox"
            aria-expanded={items.length > 0}
            aria-controls={listId}
            aria-activedescendant={items[active] ? `${listId}-${active}` : undefined}
            aria-label="Từ khóa: tên sách, độc giả hoặc màn hình"
            placeholder="Tên sách, mã độc giả hoặc màn hình…"
            value={text}
            onChange={(event) => {
              setText(event.target.value);
              setActive(0);
            }}
            onKeyDown={(event) => {
              if (event.key === "ArrowDown") {
                event.preventDefault();
                setActive((index) => Math.min(index + 1, Math.max(items.length - 1, 0)));
              } else if (event.key === "ArrowUp") {
                event.preventDefault();
                setActive((index) => Math.max(index - 1, 0));
              } else if (event.key === "Enter") {
                event.preventDefault();
                go(items[active]);
              }
            }}
          />
          <ul id={listId} role="listbox" aria-label="Kết quả tìm kiếm">
            {items.map((item, index) => (
              <li
                key={item.key}
                id={`${listId}-${index}`}
                role="option"
                aria-selected={index === active}
                className={index === active ? "active" : undefined}
                tabIndex={-1}
                onMouseEnter={() => setActive(index)}
                onClick={() => go(item)}
                onKeyDown={(event) => {
                  if (event.key === "Enter") go(item);
                }}
              >
                <span className="eyebrow">{item.group}</span>
                <strong>{item.label}</strong>
                {item.detail && <span className="muted">{item.detail}</span>}
              </li>
            ))}
          </ul>
          <p className="muted" aria-live="polite">
            {text.trim() === ""
              ? "Nhập từ khóa để tìm. ↑/↓ để chọn, Enter để mở, Esc để đóng."
              : searching
                ? "Đang tìm…"
                : items.length === 0
                  ? "Không tìm thấy"
                  : `${items.length} kết quả`}
          </p>
        </div>
      </Dialog>
    </>
  );
}
