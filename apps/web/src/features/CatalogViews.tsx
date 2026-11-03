import { useEffect, useState } from "react";
import { Badge, Button, Field, Notice, Panel, Table } from "../ui/components";
import { Icon } from "../ui/Icon";
import { PreviewAction } from "./shared";
import type { Book, ViewProps } from "./types";

export function BookCover({ book, large = false }: { book: Book; large?: boolean }) {
  return <div className={`book-cover cover-${book.color} ${large ? "cover-large" : ""}`} aria-label={`Bìa chữ: ${book.title}`}><span className="cover-edition">ẤN BẢN / {book.year}</span><div className="cover-rule" /><strong>{book.title}</strong><span className="cover-author">{book.author}</span><Icon name="book" size={24} /></div>;
}
export function CatalogView({ sample, navigate }: ViewProps) {
  const [query, setQuery] = useState("");
  const [available, setAvailable] = useState(false);
  const books = (sample?.books ?? []).filter((book) => `${book.title} ${book.author}`.toLocaleLowerCase("vi").includes(query.toLocaleLowerCase("vi")) && (!available || book.available > 0));
  return <><div className="catalog-intro"><span className="eyebrow">MỤC LỤC THƯ VIỆN</span><p>Một cuốn sách mới.<br /><em>Một góc nhìn khác.</em></p><span className="muted">Tra cứu ấn bản, tìm tác giả và xem sách sẵn có.</span></div><div className="toolbar catalog-toolbar"><Field label="Tìm sách" type="search" placeholder="Tên sách, tác giả, thể loại…" value={query} onChange={(event) => setQuery(event.target.value)} /><label className="checkbox-field"><input type="checkbox" checked={available} onChange={(event) => setAvailable(event.target.checked)} />Chỉ sách sẵn có</label></div><div className="section-heading"><h2>Khám phá danh mục</h2><span className="muted">{books.length} ấn bản</span></div>{books.length ? <div className="book-grid">{books.map((book) => <article className="book-tile" key={book.id}><button className="cover-button" onClick={() => navigate?.("FE02.02")} aria-label={`Xem ${book.title}`}><BookCover book={book} /></button><button className="book-title text-link" onClick={() => navigate?.("FE02.02")}>{book.title}</button><p className="muted">{book.author}</p><Badge tone={book.available ? "success" : "warning"}>{book.available ? `${book.available} bản khả dụng` : "Đang được mượn"}</Badge></article>)}</div> : <Panel><div className="empty-state"><Icon name="book" size={38} /><h2>Chưa có ấn bản để hiển thị</h2><p className="muted">Thử điều chỉnh từ khóa hoặc quay lại sau.</p></div></Panel>}</>;
}
export function BookView({ screen, preview, sample, navigate }: ViewProps) {
  const book = sample?.books?.[0];
  return book ? <><div className="book-detail"><BookCover book={book} large /><div><span className="eyebrow">VĂN HỌC VIỆT NAM</span><h2 className="book-detail-title">{book.title}</h2><p className="book-byline">{book.author} · {book.year}</p><Badge tone="success">{book.available} bản sẵn có</Badge><p className="book-description">Một ấn bản văn học Việt Nam trong danh mục thư viện. Xem thông tin bản sách và tình trạng khả dụng bên dưới.</p><dl className="metadata"><div><dt>Nhà xuất bản</dt><dd>—</dd></div><div><dt>Mã ấn bản</dt><dd>{book.id}</dd></div><div><dt>Ngôn ngữ</dt><dd>Tiếng Việt</dd></div></dl><PreviewAction preview={preview} navigate={navigate} receipt="FE06.02">Đặt trước ấn bản</PreviewAction></div></div><Panel title="Bản sách tại thư viện"><Table headers={["Barcode", "Tình trạng", "Lưu thông"]} rows={sample?.books ? [[`${book.id}-01`, "Tốt", "Sẵn có"], [`${book.id}-02`, "Tốt", "Đang mượn"]] : []} caption="Bản sách" /></Panel></> : <Panel title={screen.title}><Notice>Chưa có thông tin ấn bản để hiển thị.</Notice></Panel>;
}
export function CategoriesView({ preview, sample }: ViewProps) {
  const [selected, setSelected] = useState("");
  const categories = sample ? ["Văn học", "Văn học Việt Nam", "Tiểu thuyết", "Thiếu nhi", "Khoa học & công nghệ"] : [];
  return <div className="two-columns"><Panel title="Cây thể loại"><div className="category-tree">{categories.map((category, i) => <button key={category} onClick={() => setSelected(category)} className={selected === category ? "selected" : ""} style={{ paddingLeft: i === 1 || i === 2 ? 36 : 16 }}><Icon name={i < 2 ? "chevron" : "book"} size={16} />{category}</button>)}{!categories.length && <p className="muted">Chưa có thể loại.</p>}</div></Panel><Panel title="Thông tin thể loại"><Field label="Tên thể loại" value={selected} onChange={(event) => setSelected(event.target.value)} /><Field label="Thể loại cha" defaultValue="" placeholder="Chọn thể loại cha" /><Field label="Mô tả" defaultValue="" placeholder="Nhập mô tả" /><div className="actions"><PreviewAction preview={preview}>Lưu thể loại</PreviewAction></div></Panel></div>;
}
export function UploadView({ preview, sample }: ViewProps) {
  const [file, setFile] = useState<File>();
  const [error, setError] = useState("");
  const [url, setUrl] = useState("");
  useEffect(() => {
    if (!file) return;
    const objectUrl = URL.createObjectURL(file);
    setUrl(objectUrl);
    return () => URL.revokeObjectURL(objectUrl);
  }, [file]);
  const book = sample?.books?.[0];
  return <Panel title="Ảnh bìa ấn bản"><div className="upload-layout"><div>{url ? <img className="cover-large uploaded-cover" src={url} alt="Ảnh bìa đang xem trước" /> : book ? <BookCover book={book} large /> : <div className="cover-placeholder"><Icon name="book" size={40} /><span>Chưa có ảnh bìa</span></div>}</div><div><div className="upload-zone"><Icon name="download" size={32} /><h3>Chọn ảnh bìa từ thiết bị</h3><p className="muted">Ảnh JPEG, PNG hoặc WebP, tối đa 5 MB.</p><Field label="Tệp ảnh" type="file" accept="image/jpeg,image/png,image/webp" disabled={!preview} error={error} onChange={(event) => { const next = event.target.files?.[0]; if (!next) return; if (!["image/jpeg", "image/png", "image/webp"].includes(next.type) || next.size > 5 * 1024 * 1024) { setError("Chọn ảnh đúng định dạng và nhỏ hơn 5 MB."); return; } setError(""); setFile(next); }} /></div><p className="muted">Kiểm tra ảnh trước khi lưu. Ảnh hiện tại được giữ khi tải lên không thành công.</p><PreviewAction preview={preview && !!file}>Lưu ảnh bìa</PreviewAction></div></div></Panel>;
}
