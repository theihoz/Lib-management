import { useEffect, useId, useRef } from "react";
import type { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode } from "react";
import { Icon } from "./Icon";

export type Book = {
  id: string;
  title: string;
  author: string;
  year: string;
  available: number;
  color: string;
};
export function BookCover({ book, large = false }: { book: Book; large?: boolean }) {
  return (
    <div
      className={`book-cover cover-${book.color} ${large ? "cover-large" : ""}`}
      aria-label={`Bìa chữ: ${book.title}`}
    >
      <span className="cover-edition">ẤN BẢN / {book.year}</span>
      <div className="cover-rule" />
      <strong>{book.title}</strong>
      <span className="cover-author">{book.author}</span>
      <Icon name="book" size={24} />
    </div>
  );
}

export function Button({
  variant = "primary",
  icon,
  children,
  className = "",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "ghost" | "danger";
  icon?: string;
}) {
  return (
    <button type="button" className={`button button-${variant} ${className}`} {...props}>
      {icon && <Icon name={icon} size={18} />}
      {children}
    </button>
  );
}
export function Badge({
  children,
  tone = "neutral",
}: {
  children: ReactNode;
  tone?: "success" | "warning" | "danger" | "neutral";
}) {
  return (
    <span className={`badge badge-${tone}`}>
      <span className="status-dot" />
      {children}
    </span>
  );
}
export function Panel({
  title,
  subtitle,
  children,
  className = "",
}: {
  title?: string;
  subtitle?: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={`panel ${className}`}>
      {title && (
        <header className="panel-heading">
          <h2>{title}</h2>
          {subtitle && <p className="muted">{subtitle}</p>}
        </header>
      )}
      {children}
    </section>
  );
}
export function Field({
  label,
  hint,
  error,
  ...props
}: InputHTMLAttributes<HTMLInputElement> & { label: string; hint?: string; error?: string }) {
  const uid = useId();
  return (
    <div className="field">
      <label htmlFor={uid}>{label}</label>
      <input
        id={uid}
        aria-invalid={error ? true : undefined}
        aria-describedby={hint || error ? `${uid}-hint` : undefined}
        {...props}
      />
      {(hint || error) && (
        <small id={`${uid}-hint`} className={error ? "text-danger" : "muted"}>
          {error ?? hint}
        </small>
      )}
    </div>
  );
}
export function Table({
  headers,
  rows,
  caption = "Danh sách",
  onRow,
  empty,
}: {
  headers: string[];
  rows: string[][];
  caption?: string;
  onRow?: (index: number) => void;
  /** Empty-state text, e.g. "Không tìm thấy" for a search with no match (QĐ23). */
  empty?: { title: string; hint: string };
}) {
  return (
    <div
      className="table-scroll"
      role="region"
      aria-label={`${caption}, có thể cuộn ngang`}
      tabIndex={0}
    >
      <table>
        <caption className="sr-only">{caption}</caption>
        <thead>
          <tr>
            {headers.map((header) => (
              <th scope="col" key={header}>
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.length ? (
            rows.map((row, i) => (
              <tr key={`${row[0] ?? "row"}-${i}`}>
                {headers.map((header, j) => (
                  <td key={header}>
                    {j === 0 && onRow ? (
                      <button className="text-link" onClick={() => onRow(i)}>
                        {row[j] ?? "—"}
                      </button>
                    ) : (
                      (row[j] ?? "—")
                    )}
                  </td>
                ))}
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan={headers.length}>
                <div className="empty-state">
                  <Icon name="archive" size={30} />
                  <strong>{empty?.title ?? "Chưa có dữ liệu"}</strong>
                  <span className="muted">
                    {empty?.hint ?? "Các mục sẽ xuất hiện tại đây khi có dữ liệu."}
                  </span>
                </div>
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
export function Notice({
  children,
  tone = "info",
}: {
  children: ReactNode;
  tone?: "info" | "warning" | "danger";
}) {
  return (
    <div className={`notice notice-${tone}`} role={tone === "danger" ? "alert" : "status"}>
      <Icon name={tone === "info" ? "book" : "alert"} size={18} />
      <div>{children}</div>
    </div>
  );
}
export function Dialog({
  open,
  title,
  children,
  onClose,
  pending = false,
}: {
  open: boolean;
  title: string;
  children: ReactNode;
  onClose: () => void;
  pending?: boolean;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  const titleId = useId();
  useEffect(() => {
    const dialog = ref.current;
    if (!dialog || !open) return;
    const previous = document.activeElement;
    if (typeof dialog.showModal === "function") dialog.showModal();
    else dialog.setAttribute("open", "");
    return () => {
      if (typeof dialog.close === "function") dialog.close();
      else dialog.removeAttribute("open");
      if (previous instanceof HTMLElement && previous.isConnected) previous.focus();
    };
  }, [open]);
  return (
    <dialog
      ref={ref}
      aria-labelledby={titleId}
      onCancel={(event) => {
        event.preventDefault();
        if (!pending) onClose();
      }}
    >
      <div className="dialog-heading">
        <h2 id={titleId}>{title}</h2>
        <Button
          variant="ghost"
          icon="close"
          aria-label="Đóng"
          onClick={onClose}
          disabled={pending}
        />
      </div>
      {children}
    </dialog>
  );
}
export function Stats({ items }: { items: { label: string; value: string; note?: string }[] }) {
  return (
    <div className="stats-grid">
      {items.map((item) => (
        <div className="stat" key={item.label}>
          <span className="eyebrow">{item.label}</span>
          <strong>{item.value}</strong>
          {item.note && <small className="muted">{item.note}</small>}
        </div>
      ))}
    </div>
  );
}
export function ProgressSteps({
  current = 1,
  items = ["Xác định độc giả", "Chọn sách", "Xác nhận", "Biên nhận"],
}: {
  current?: number;
  items?: string[];
}) {
  return (
    <ol className="journey">
      {items.map((step, i) => (
        <li
          key={step}
          aria-current={i === current ? "step" : undefined}
          className={i <= current ? "is-current" : ""}
        >
          <span>{i < current ? <Icon name="check" size={15} /> : i + 1}</span>
          {step}
        </li>
      ))}
    </ol>
  );
}
