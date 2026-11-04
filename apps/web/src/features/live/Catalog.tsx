import { useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router";
import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useServices, useSession } from "../../auth/session";
import { createIdempotencyKey } from "../../api/idempotency";
import type { components } from "../../api/schema";
import { useDebounced } from "../../lib/useDebounced";
import { Badge, BookCover, Button, Dialog, Field, Notice, Panel, Table } from "../../ui/components";
import type { Book } from "../../ui/components";
import type { ScreenDefinition } from "../types";
import { ApiFailure, LoadingSkeleton, MutationFeedback } from "./common";
import { MANUAL_COPY_STATUS, copyStatus, type ManualCopyStatus } from "./labels";

type Edition = components["schemas"]["PublicEdition"];
function editionCover(item: Edition): Book {
  return {
    id: item.id,
    title: item.title,
    year: String(item.publication_year),
    author: item.authors?.map((author) => author.name).join(", ") ?? "Chưa có tác giả",
    available: item.availability?.availableCount ?? 0,
    color: ["sand", "sage", "clay", "sky"][item.title.length % 4]!,
  };
}
function EditionList({ staff = false }: { staff?: boolean }) {
  const services = useServices();
  const session = useSession();
  const navigate = useNavigate();
  const [search, setSearch] = useState("");
  // QĐ23: a blank or whitespace keyword is not a search; the list is browsed instead.
  const query = useDebounced(search).trim() || undefined;
  const notFound = {
    title: "Không tìm thấy",
    hint: "Không có sách phù hợp với từ khóa. Thử tên sách, tác giả hoặc ISBN khác.",
  };
  const [categoryId, setCategoryId] = useState("");
  const filtered = !!query || !!categoryId;
  const categories = useQuery({
    queryKey: ["catalog", "categories", "filter"],
    queryFn: async ({ signal }) =>
      (await services.catalog.get_categories({ params: { query: { limit: 100 } }, signal })).data!
        .data,
    staleTime: 5 * 60_000,
  });
  const result = useInfiniteQuery({
    queryKey: ["catalog", "editions", query, categoryId],
    initialPageParam: undefined as string | undefined,
    queryFn: async ({ pageParam, signal }) =>
      (
        await services.catalog.get_book_editions({
          params: {
            query: {
              query,
              categoryId: categoryId || undefined,
              cursor: pageParam,
              limit: 20,
            },
          },
          signal,
        })
      ).data!,
    getNextPageParam: (page) => page.nextCursor ?? undefined,
    staleTime: staff ? 30_000 : 5 * 60_000,
  });
  const items = result.data?.pages.flatMap((page) => page.data) ?? [];
  return (
    <div className="stack">
      <div className="toolbar">
        <Field
          label="Tìm sách"
          type="search"
          placeholder="Tên sách, tác giả hoặc ISBN…"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
        />
        <div className="field">
          <label htmlFor="edition-category-filter">Thể loại</label>
          <select
            id="edition-category-filter"
            value={categoryId}
            onChange={(event) => setCategoryId(event.target.value)}
          >
            <option value="">Tất cả thể loại</option>
            {categories.data?.map((category) => (
              <option key={category.id} value={category.id}>
                {category.code} · {category.name}
              </option>
            ))}
          </select>
        </div>
        {session.permissions.includes("catalog.write") && (
          <Link className="button button-primary" to="/staff/catalog/editions/new">
            Thêm ấn bản
          </Link>
        )}
      </div>
      {result.isPending ? (
        <LoadingSkeleton books={!staff} />
      ) : result.error ? (
        <ApiFailure
          error={result.error}
          retry={() => {
            void result.refetch();
          }}
        />
      ) : staff ? (
        <Panel>
          <Table
            headers={["Mã ấn bản", "Nhan đề", "Tác giả", "Năm", "Khả dụng"]}
            empty={filtered ? notFound : undefined}
            rows={items.map((item) => [
              item.id,
              item.title,
              item.authors?.map((author) => author.name).join(", ") ?? "—",
              String(item.publication_year),
              String(item.availability?.availableCount ?? 0),
            ])}
            onRow={(index) => {
              void navigate(`/catalog/${items[index]!.id}`);
            }}
            caption="Danh mục ấn bản"
          />
        </Panel>
      ) : items.length ? (
        <div className="book-grid">
          {items.map((item) => (
            <article key={item.id} className="book-tile">
              <Link
                className="cover-button"
                to={`/catalog/${item.id}`}
                aria-label={`Xem ${item.title}`}
              >
                <BookCover book={editionCover(item)} />
              </Link>
              <Link className="book-title" to={`/catalog/${item.id}`}>
                {item.title}
              </Link>
              <p className="muted">{editionCover(item).author}</p>
              <Badge tone={item.availability?.availableCount ? "success" : "warning"}>
                {item.availability?.availableCount ?? 0} bản khả dụng
              </Badge>
            </article>
          ))}
        </div>
      ) : (
        <Panel>
          <div className="empty-state">
            <h2>{filtered ? notFound.title : "Chưa có ấn bản"}</h2>
            <p>{filtered ? notFound.hint : "Các ấn bản sẽ xuất hiện tại đây khi có dữ liệu."}</p>
          </div>
        </Panel>
      )}
      {result.hasNextPage && (
        <Button
          variant="secondary"
          disabled={result.isFetchingNextPage}
          onClick={() => {
            void result.fetchNextPage();
          }}
        >
          {result.isFetchingNextPage ? "Đang tải…" : "Tải thêm 20 ấn bản"}
        </Button>
      )}
    </div>
  );
}
function EditionDetail() {
  const { editionId = "" } = useParams();
  const services = useServices();
  const session = useSession();
  const navigate = useNavigate();
  const cache = useQueryClient();
  const [confirm, setConfirm] = useState(false);
  // D4: "xóa" means stop using; history is kept (Lab 3 RESTRICT).
  const deactivate = useMutation({
    mutationFn: async (version: number) =>
      (
        await services.catalog.patch_book_editions_id({
          params: { path: { id: editionId } },
          body: { expectedVersion: version, status: "INACTIVE" },
        })
      ).data!,
    onSuccess: () => {
      setConfirm(false);
      void cache.invalidateQueries({ queryKey: ["catalog"] });
      void navigate("/staff/catalog");
    },
    onError: () => setConfirm(false),
  });
  const result = useQuery({
    queryKey: ["catalog", "edition", editionId],
    queryFn: async ({ signal }) =>
      (await services.catalog.get_book_editions_id({ params: { path: { id: editionId } }, signal }))
        .data!,
  });
  if (result.isPending) return <LoadingSkeleton />;
  if (result.error)
    return (
      <ApiFailure
        error={result.error}
        retry={() => {
          void result.refetch();
        }}
      />
    );
  const book = result.data;
  return (
    <div className="stack">
      <div className="book-detail">
        <BookCover book={editionCover(book)} large />
        <div>
          <span className="eyebrow">ẤN BẢN THƯ VIỆN</span>
          <h2 className="book-detail-title">{book.title}</h2>
          <p className="book-byline">
            {editionCover(book).author} · {book.publication_year}
          </p>
          <Badge tone={book.availability?.availableCount ? "success" : "warning"}>
            {book.availability?.availableCount ?? 0} bản sẵn có
          </Badge>
          <p className="book-description">{book.description || "Chưa có mô tả cho ấn bản này."}</p>
          <dl className="metadata">
            <div>
              <dt>ISBN</dt>
              <dd>{book.isbn ?? "—"}</dd>
            </div>
            <div>
              <dt>Ngôn ngữ</dt>
              <dd>{book.language ?? "—"}</dd>
            </div>
          </dl>
          {session.permissions.includes("catalog.write") && (
            <div className="actions">
              <Link
                className="button button-secondary"
                to={`/staff/catalog/copies?edition=${book.id}`}
              >
                Quản lý bản sách
              </Link>
              <Button variant="secondary" onClick={() => setConfirm(true)}>
                Ngừng dùng ấn bản
              </Button>
            </div>
          )}
          <MutationFeedback error={deactivate.error} />
        </div>
      </div>
      <Dialog
        open={confirm}
        title="Ngừng dùng ấn bản"
        pending={deactivate.isPending}
        onClose={() => setConfirm(false)}
      >
        <p>
          Ấn bản <strong>{book.title}</strong> sẽ không còn hiện trong tra cứu. Lịch sử mượn trả
          được giữ nguyên; không thể ngừng dùng khi còn bản sách đang mượn hoặc giữ chỗ.
        </p>
        <div className="actions">
          <Button
            disabled={deactivate.isPending}
            onClick={() => deactivate.mutate(book.version ?? 1)}
          >
            Xác nhận ngừng dùng
          </Button>
          <Button variant="secondary" onClick={() => setConfirm(false)}>
            Quay lại
          </Button>
        </div>
      </Dialog>
    </div>
  );
}
function EditionForm() {
  const services = useServices();
  const cache = useQueryClient();
  const key = useRef(createIdempotencyKey()).current;
  const year = new Date().getFullYear();
  const [body, setBody] = useState<components["schemas"]["BookEditionCreate"]>({
    title: "",
    publicationYear: year,
    isbn: "",
    description: "",
    language: "vi",
  });
  const lookup = useQuery({
    queryKey: ["catalog", "form-lookups"],
    queryFn: async ({ signal }) => {
      const [authors, publishers, categories] = await Promise.all([
        services.catalog.get_authors({ params: { query: { limit: 100 } }, signal }),
        services.catalog.get_publishers({ params: { query: { limit: 100 } }, signal }),
        services.catalog.get_categories({ params: { query: { limit: 100 } }, signal }),
      ]);
      return {
        authors: authors.data?.data ?? [],
        publishers: publishers.data?.data ?? [],
        categories: categories.data?.data ?? [],
      };
    },
  });
  const save = useMutation({
    mutationFn: async () =>
      (
        await services.catalog.post_book_editions({
          body,
          params: { header: { "Idempotency-Key": key.forPayload(body) } },
        })
      ).data!,
    onSuccess: () => {
      key.reset();
      void cache.invalidateQueries({ queryKey: ["catalog"] });
    },
  });
  return (
    <Panel title="Thông tin ấn bản">
      <form
        onSubmit={(event) => {
          event.preventDefault();
          save.mutate();
        }}
      >
        <div className="form-grid">
          <Field
            label="Nhan đề"
            required
            maxLength={300}
            value={body.title}
            onChange={(event) => setBody({ ...body, title: event.target.value })}
          />
          <Field
            label="Năm xuất bản"
            required
            type="number"
            min={year - 8}
            max={year}
            value={body.publicationYear}
            onChange={(event) => setBody({ ...body, publicationYear: Number(event.target.value) })}
          />
          <Field
            label="ISBN"
            maxLength={13}
            value={body.isbn ?? ""}
            onChange={(event) => setBody({ ...body, isbn: event.target.value || null })}
          />
          <Field
            label="Ngôn ngữ"
            maxLength={32}
            value={body.language ?? ""}
            onChange={(event) => setBody({ ...body, language: event.target.value })}
          />
          <div className="field">
            <label htmlFor="edition-author">Tác giả</label>
            <select
              id="edition-author"
              multiple
              value={body.authorIds ?? []}
              onChange={(event) =>
                setBody({
                  ...body,
                  authorIds: Array.from(event.target.selectedOptions, (option) => option.value),
                })
              }
            >
              {lookup.data?.authors.map((author) => (
                <option key={author.id} value={author.id}>
                  {author.name}
                </option>
              ))}
            </select>
            <small className="muted">Có thể chọn nhiều tác giả.</small>
          </div>
          <div className="field">
            <label htmlFor="edition-publisher">Nhà xuất bản</label>
            <select
              id="edition-publisher"
              value={body.publisherId ?? ""}
              onChange={(event) => setBody({ ...body, publisherId: event.target.value || null })}
            >
              <option value="">Chưa chọn</option>
              {lookup.data?.publishers.map((publisher) => (
                <option key={publisher.id} value={publisher.id}>
                  {publisher.name}
                </option>
              ))}
            </select>
          </div>
          <div className="field">
            <label htmlFor="edition-category">Thể loại</label>
            <select
              id="edition-category"
              multiple
              value={body.categoryIds ?? []}
              onChange={(event) =>
                setBody({
                  ...body,
                  categoryIds: Array.from(event.target.selectedOptions, (option) => option.value),
                })
              }
            >
              {lookup.data?.categories.map((category) => (
                <option key={category.id} value={category.id}>
                  {category.name}
                </option>
              ))}
            </select>
          </div>
          <Field
            label="Mô tả"
            value={body.description ?? ""}
            onChange={(event) => setBody({ ...body, description: event.target.value })}
          />
        </div>
        {lookup.error && (
          <Notice tone="warning">
            Chưa tải được danh sách tác giả, nhà xuất bản hoặc thể loại. Hãy thử lại trước khi chọn.
          </Notice>
        )}
        <MutationFeedback error={save.error} success={save.isSuccess}>
          {save.data && <Link to={`/catalog/${save.data.id}`}>Đã tạo ấn bản. Mở chi tiết.</Link>}
        </MutationFeedback>
        <div className="actions">
          <Button type="submit" disabled={save.isPending} aria-busy={save.isPending}>
            {save.isPending ? "Đang lưu…" : "Lưu ấn bản"}
          </Button>
          <Link className="button button-secondary" to="/staff/catalog">
            Về danh mục
          </Link>
        </div>
      </form>
    </Panel>
  );
}
function ReferenceList({ type }: { type: "authors" | "publishers" | "categories" }) {
  const services = useServices();
  const cache = useQueryClient();
  const key = useRef(createIdempotencyKey()).current;
  const [search, setSearch] = useState("");
  const query = useDebounced(search);
  const [name, setName] = useState("");
  const [detail, setDetail] = useState("");
  const [parentId, setParentId] = useState("");
  // QĐ04: a new category hangs below main category A, B or C (or one of their branches).
  const parents = useQuery({
    queryKey: ["catalog", "categories", "parents"],
    enabled: type === "categories",
    queryFn: async ({ signal }) =>
      (await services.catalog.get_categories({ params: { query: { limit: 100 } }, signal })).data!
        .data,
  });
  const result = useInfiniteQuery({
    queryKey: ["catalog", type, query],
    initialPageParam: undefined as string | undefined,
    queryFn: async ({ pageParam, signal }) => {
      const options = { params: { query: { query, cursor: pageParam, limit: 20 } }, signal };
      const response = await (type === "authors"
        ? services.catalog.get_authors(options)
        : type === "publishers"
          ? services.catalog.get_publishers(options)
          : services.catalog.get_categories(options));
      return {
        data: response.data!.data.map((item) => ({
          id: item.id,
          name: item.name,
          status: "status" in item ? item.status : "Phân loại",
        })),
        nextCursor: response.data!.nextCursor,
      };
    },
    getNextPageParam: (page) => page.nextCursor ?? undefined,
  });
  const save = useMutation({
    mutationFn: async () => {
      const header = { "Idempotency-Key": key.forPayload({ name, detail, parentId }) };
      return type === "authors"
        ? services.catalog.post_authors({
            body: { name, biography: detail || null },
            params: { header },
          })
        : type === "publishers"
          ? services.catalog.post_publishers({
              body: { name, address: detail || null },
              params: { header },
            })
          : services.catalog.post_categories({
              body: { name, code: detail, parentId },
              params: { header },
            });
    },
    onSuccess: () => {
      key.reset();
      setName("");
      setDetail("");
      setParentId("");
      void cache.invalidateQueries({ queryKey: ["catalog"] });
    },
  });
  const rows =
    result.data?.pages
      .flatMap((page) => page.data)
      .map((item) => [item.id, item.name, item.status]) ?? [];
  return (
    <div className="stack">
      <Field
        label="Tìm kiếm"
        type="search"
        value={search}
        onChange={(event) => setSearch(event.target.value)}
      />
      {result.isPending ? (
        <LoadingSkeleton />
      ) : result.error ? (
        <ApiFailure
          error={result.error}
          retry={() => {
            void result.refetch();
          }}
        />
      ) : (
        <Panel>
          <Table headers={["Mã", "Tên", "Trạng thái"]} rows={rows} />
          {result.hasNextPage && (
            <Button
              variant="secondary"
              onClick={() => {
                void result.fetchNextPage();
              }}
              disabled={result.isFetchingNextPage}
            >
              Tải thêm
            </Button>
          )}
        </Panel>
      )}
      <Panel title="Thêm thông tin danh mục">
        <form
          onSubmit={(event) => {
            event.preventDefault();
            save.mutate();
          }}
        >
          <div className="form-grid">
            <Field
              label="Tên"
              required
              maxLength={200}
              value={name}
              onChange={(event) => setName(event.target.value)}
            />
            <Field
              label={
                type === "publishers"
                  ? "Địa chỉ"
                  : type === "categories"
                    ? "Mã thể loại"
                    : "Giới thiệu"
              }
              value={detail}
              required={type === "categories"}
              onChange={(event) => setDetail(event.target.value)}
            />
            {type === "categories" && (
              <div className="field">
                <label htmlFor="category-parent">Thuộc thể loại (A, B, C hoặc nhánh con)</label>
                <select
                  id="category-parent"
                  required
                  value={parentId}
                  onChange={(event) => setParentId(event.target.value)}
                >
                  <option value="">— Chọn thể loại cha —</option>
                  {parents.data?.map((category) => (
                    <option key={category.id} value={category.id}>
                      {category.code} · {category.name}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>
          <MutationFeedback error={save.error} success={save.isSuccess} />
          <Button type="submit" disabled={save.isPending}>
            Lưu thông tin
          </Button>
        </form>
      </Panel>
    </div>
  );
}
function Copies() {
  const services = useServices();
  const cache = useQueryClient();
  const key = useRef(createIdempotencyKey()).current;
  const [edition, setEdition] = useState(
    new URLSearchParams(window.location.search).get("edition") ?? "",
  );
  const [barcodes, setBarcodes] = useState("");
  const [location, setLocation] = useState("");
  const result = useInfiniteQuery({
    queryKey: ["catalog", "copies", edition],
    initialPageParam: undefined as string | undefined,
    enabled: !!edition,
    queryFn: async ({ pageParam, signal }) =>
      (
        await services.catalog.get_book_editions_id_copies({
          params: { path: { id: edition }, query: { cursor: pageParam, limit: 20 } },
          signal,
        })
      ).data!,
    getNextPageParam: (page) => page.nextCursor ?? undefined,
  });
  const save = useMutation({
    mutationFn: async () => {
      const body = {
        barcodes: barcodes
          .split(/[\n,]+/)
          .map((item) => item.trim())
          .filter(Boolean),
        locationId: location,
      };
      return (
        await services.catalog.post_book_editions_id_copies({
          params: {
            path: { id: edition },
            header: { "Idempotency-Key": key.forPayload({ edition, ...body }) },
          },
          body,
        })
      ).data!;
    },
    onSuccess: () => {
      key.reset();
      setBarcodes("");
      void cache.invalidateQueries({ queryKey: ["catalog"] });
    },
  });
  const copies = result.data?.pages.flatMap((page) => page.data) ?? [];
  const statusKey = useRef(createIdempotencyKey()).current;
  const [target, setTarget] = useState<(typeof copies)[number]>();
  const [next, setNext] = useState<ManualCopyStatus>("AVAILABLE");
  const [reason, setReason] = useState("");
  const locked = !!target && !(MANUAL_COPY_STATUS as readonly string[]).includes(target.status);
  const change = useMutation({
    mutationFn: async () => {
      const body = {
        expectedVersion: target!.version,
        status: next,
        reason: reason.trim() || null,
      };
      return (
        await services.catalog.patch_copies_id({
          params: {
            path: { id: target!.id },
            header: { "Idempotency-Key": statusKey.forPayload({ id: target!.id, ...body }) },
          },
          body,
        })
      ).data!;
    },
    onSuccess: () => {
      statusKey.reset();
      setTarget(undefined);
      void cache.invalidateQueries({ queryKey: ["catalog"] });
    },
  });
  return (
    <div className="stack">
      <Field
        label="Mã ấn bản"
        value={edition}
        onChange={(event) => setEdition(event.target.value)}
        placeholder="Chọn từ trang chi tiết ấn bản"
      />
      {result.isFetching ? (
        <LoadingSkeleton />
      ) : result.error ? (
        <ApiFailure error={result.error} />
      ) : (
        <Panel>
          <Table
            caption="Bản sách của ấn bản"
            headers={["Barcode", "Tình trạng", "Vị trí"]}
            rows={copies.map((copy) => [
              copy.barcode,
              copyStatus(copy.status),
              copy.location_id ?? "—",
            ])}
            onRow={(index) => {
              const picked = copies[index];
              if (!picked) return;
              setTarget(picked);
              setNext(picked.status === "AVAILABLE" ? "REPAIR" : "AVAILABLE");
              setReason("");
              change.reset();
            }}
          />
          <p className="muted">
            Bấm mã vạch để đổi trạng thái (Sẵn sàng/Hỏng/Bảo trì/Mất). Bản đang mượn, đang giữ chỗ
            hoặc đã thanh lý không đổi tay được.
          </p>
          {result.hasNextPage && (
            <Button
              onClick={() => {
                void result.fetchNextPage();
              }}
            >
              Tải thêm
            </Button>
          )}
        </Panel>
      )}
      <MutationFeedback error={undefined} success={change.isSuccess}>
        Đã đổi trạng thái bản sách.
      </MutationFeedback>
      <Dialog
        open={!!target}
        title={`Đổi trạng thái bản ${target?.barcode ?? ""}`}
        pending={change.isPending}
        onClose={() => setTarget(undefined)}
      >
        {locked ? (
          <Notice tone="warning">
            Bản sách đang ở trạng thái “{copyStatus(target.status)}”; trạng thái này chỉ đổi qua
            mượn/trả/giữ chỗ hoặc thanh lý.
          </Notice>
        ) : (
          <form
            onSubmit={(event) => {
              event.preventDefault();
              change.mutate();
            }}
          >
            <p>Hiện tại: {target ? copyStatus(target.status) : ""}</p>
            <div className="field">
              <label htmlFor="copy-next-status">Trạng thái mới</label>
              <select
                id="copy-next-status"
                value={next}
                onChange={(event) => setNext(event.target.value as ManualCopyStatus)}
              >
                {MANUAL_COPY_STATUS.filter((code) => code !== target?.status).map((code) => (
                  <option key={code} value={code}>
                    {copyStatus(code)}
                  </option>
                ))}
              </select>
            </div>
            <Field
              label="Lý do"
              required={next !== "AVAILABLE"}
              maxLength={500}
              value={reason}
              hint={next === "AVAILABLE" ? "Không bắt buộc khi đưa về Sẵn sàng." : undefined}
              onChange={(event) => setReason(event.target.value)}
            />
            <MutationFeedback error={change.error} />
            <div className="actions">
              <Button type="submit" disabled={change.isPending}>
                {change.isPending ? "Đang lưu…" : "Lưu trạng thái"}
              </Button>
              <Button variant="secondary" onClick={() => setTarget(undefined)}>
                Hủy
              </Button>
            </div>
          </form>
        )}
      </Dialog>
      <Panel title="Thêm bản sách">
        <form
          onSubmit={(event) => {
            event.preventDefault();
            save.mutate();
          }}
        >
          <div className="form-grid">
            <Field
              label="Barcode, phân cách bằng dấu phẩy"
              required
              value={barcodes}
              onChange={(event) => setBarcodes(event.target.value)}
            />
            <Field
              label="Mã vị trí trong kho"
              required
              value={location}
              onChange={(event) => setLocation(event.target.value)}
            />
          </div>
          <MutationFeedback error={save.error} success={save.isSuccess} />
          <Button type="submit" disabled={save.isPending || !edition}>
            Thêm bản sách
          </Button>
        </form>
      </Panel>
    </div>
  );
}
export default function Catalog({ screen }: { screen: ScreenDefinition }) {
  if (screen.id === "FE02.01") return <EditionList />;
  if (screen.id === "FE02.02") return <EditionDetail />;
  if (screen.id === "FE02.03") return <EditionList staff />;
  if (screen.id === "FE02.04") return <EditionForm />;
  if (screen.id === "FE02.05") return <Copies />;
  return (
    <ReferenceList
      type={
        screen.id === "FE02.06" ? "authors" : screen.id === "FE02.07" ? "publishers" : "categories"
      }
    />
  );
}
