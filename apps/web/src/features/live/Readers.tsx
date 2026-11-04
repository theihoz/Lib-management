import { useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router";
import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useServices, useSession } from "../../auth/session";
import { createIdempotencyKey } from "../../api/idempotency";
import type { components } from "../../api/schema";
import { useDebounced } from "../../lib/useDebounced";
import { Badge, Button, Field, Panel, Table } from "../../ui/components";
import type { ScreenDefinition } from "../types";
import { ApiFailure, LoadingSkeleton, MutationFeedback } from "./common";

function ReaderList() {
  const services = useServices();
  const session = useSession();
  const navigate = useNavigate();
  const [search, setSearch] = useState("");
  const query = useDebounced(search);
  const result = useInfiniteQuery({
    queryKey: ["readers", query],
    initialPageParam: undefined as string | undefined,
    queryFn: async ({ pageParam, signal }) =>
      (
        await services.readers.get_readers({
          params: { query: { query, cursor: pageParam, limit: 20 } },
          signal,
        })
      ).data!,
    getNextPageParam: (page) => page.nextCursor ?? undefined,
  });
  const readers = result.data?.pages.flatMap((page) => page.data) ?? [];
  return (
    <div className="stack">
      <div className="toolbar">
        <Field
          label="Tìm độc giả"
          type="search"
          placeholder="Họ tên, mã độc giả hoặc email…"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
        />
        {session.permissions.includes("reader.write") && (
          <Link className="button button-primary" to="/staff/readers/new">
            Thêm độc giả
          </Link>
        )}
      </div>
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
          <Table
            headers={["Mã độc giả", "Họ tên", "Email", "Loại", "Trạng thái"]}
            rows={readers.map((reader) => [
              reader.reader_code,
              reader.full_name,
              reader.email ?? "—",
              reader.reader_type,
              reader.status,
            ])}
            onRow={(index) => {
              void navigate(`/staff/readers/${readers[index]!.id}`);
            }}
            caption="Độc giả thư viện"
          />
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
          Tải thêm 20 độc giả
        </Button>
      )}
    </div>
  );
}
function ReaderForm() {
  const services = useServices();
  const cache = useQueryClient();
  const key = useRef(createIdempotencyKey()).current;
  const [body, setBody] = useState<components["schemas"]["ReaderCreate"]>({
    readerCode: "",
    fullName: "",
    birthDate: "",
    readerType: "X",
    email: "",
    phone: "",
    address: "",
  });
  const save = useMutation({
    mutationFn: async () =>
      (
        await services.readers.post_readers({
          body: {
            ...body,
            email: body.email || null,
            phone: body.phone || null,
            address: body.address || null,
          },
          params: { header: { "Idempotency-Key": key.forPayload(body) } },
        })
      ).data!,
    onSuccess: () => {
      key.reset();
      void cache.invalidateQueries({ queryKey: ["readers"] });
    },
  });
  return (
    <Panel title="Hồ sơ độc giả">
      <form
        onSubmit={(event) => {
          event.preventDefault();
          save.mutate();
        }}
      >
        <div className="form-grid">
          <Field
            label="Mã độc giả"
            required
            maxLength={32}
            value={body.readerCode}
            onChange={(event) => setBody({ ...body, readerCode: event.target.value })}
          />
          <Field
            label="Họ tên"
            required
            maxLength={200}
            value={body.fullName}
            onChange={(event) => setBody({ ...body, fullName: event.target.value })}
          />
          <Field
            label="Ngày sinh"
            required
            type="date"
            value={body.birthDate}
            max={new Date().toISOString().slice(0, 10)}
            hint="Độc giả từ 12 đến 55 tuổi (QĐ01)."
            onChange={(event) => setBody({ ...body, birthDate: event.target.value })}
          />
          <div className="field">
            <label htmlFor="reader-type">Loại độc giả</label>
            <select
              id="reader-type"
              value={body.readerType}
              onChange={(event) =>
                setBody({
                  ...body,
                  readerType: event.target
                    .value as components["schemas"]["ReaderCreate"]["readerType"],
                })
              }
            >
              <option value="X">X</option>
              <option value="Y">Y</option>
              <option value="Z">Z</option>
            </select>
          </div>
          <Field
            label="Email"
            type="email"
            value={body.email ?? ""}
            onChange={(event) => setBody({ ...body, email: event.target.value })}
          />
          <Field
            label="Điện thoại"
            type="tel"
            value={body.phone ?? ""}
            onChange={(event) => setBody({ ...body, phone: event.target.value })}
          />
          <Field
            label="Địa chỉ"
            value={body.address ?? ""}
            onChange={(event) => setBody({ ...body, address: event.target.value })}
          />
        </div>
        <MutationFeedback error={save.error} success={save.isSuccess}>
          {save.data && (
            <Link to={`/staff/readers/${save.data.id}`}>Đã tạo hồ sơ. Mở chi tiết độc giả.</Link>
          )}
        </MutationFeedback>
        <div className="actions">
          <Button type="submit" disabled={save.isPending} aria-busy={save.isPending}>
            {save.isPending ? "Đang lưu…" : "Lưu hồ sơ"}
          </Button>
          <Link className="button button-secondary" to="/staff/readers">
            Về danh sách
          </Link>
        </div>
      </form>
    </Panel>
  );
}
function ReaderProfile() {
  const { readerId = "" } = useParams();
  const services = useServices();
  const session = useSession();
  const reader = useQuery({
    queryKey: ["reader", readerId],
    queryFn: async ({ signal }) =>
      (await services.readers.get_readers_id({ params: { path: { id: readerId } }, signal })).data!,
  });
  const eligibility = useQuery({
    queryKey: ["reader", readerId, "eligibility"],
    queryFn: async ({ signal }) =>
      (
        await services.readers.get_readers_id_eligibility({
          params: { path: { id: readerId } },
          signal,
        })
      ).data!,
    enabled: session.permissions.includes("eligibility.read"),
    staleTime: 0,
  });
  if (reader.isPending) return <LoadingSkeleton />;
  if (reader.error) return <ApiFailure error={reader.error} />;
  return (
    <div className="stack">
      <Panel title={reader.data.full_name} subtitle={reader.data.reader_code}>
        <Badge tone={reader.data.status === "ACTIVE" ? "success" : "warning"}>
          {reader.data.status}
        </Badge>
        <dl className="detail-list">
          {[
            ["Email", reader.data.email],
            ["Điện thoại", reader.data.phone],
            ["Ngày sinh", reader.data.birth_date],
            ["Loại độc giả", reader.data.reader_type],
            ["Địa chỉ", reader.data.address],
          ].map(([label, value]) => (
            <div key={label}>
              <dt>{label}</dt>
              <dd>{value ?? "—"}</dd>
            </div>
          ))}
        </dl>
        <div className="live-data-links">
          {session.permissions.includes("card.issue") && (
            <Link
              className="button button-secondary"
              to={`/staff/readers/cards/new?reader=${readerId}`}
            >
              Cấp thẻ thư viện
            </Link>
          )}
          {session.permissions.includes("loan.checkout") && (
            <Link className="button button-primary" to={`/staff/checkout?reader=${readerId}`}>
              Lập phiếu mượn
            </Link>
          )}
        </div>
      </Panel>
      {eligibility.data && (
        <Panel title="Điều kiện mượn">
          <Badge tone={eligibility.data.allowed ? "success" : "warning"}>
            {eligibility.data.allowed ? "Đủ điều kiện" : "Chưa đủ điều kiện"}
          </Badge>
          <ul>
            {eligibility.data.reasons.map((reason) => (
              <li key={reason}>{reason}</li>
            ))}
          </ul>
        </Panel>
      )}
      {eligibility.error && (
        <ApiFailure
          error={eligibility.error}
          retry={() => {
            void eligibility.refetch();
          }}
        />
      )}
    </div>
  );
}
function IssueCard() {
  const services = useServices();
  const cache = useQueryClient();
  const key = useRef(createIdempotencyKey()).current;
  const [reader, setReader] = useState(
    new URLSearchParams(window.location.search).get("reader") ?? "",
  );
  const save = useMutation({
    mutationFn: async () =>
      (
        await services.readers.post_readers_id_cards({
          params: {
            path: { id: reader },
            header: { "Idempotency-Key": key.forPayload({ reader }) },
          },
        })
      ).data!,
    onSuccess: () => {
      key.reset();
      void cache.invalidateQueries({ queryKey: ["reader", reader] });
    },
  });
  return (
    <Panel title="Cấp thẻ thư viện">
      <form
        onSubmit={(event) => {
          event.preventDefault();
          save.mutate();
        }}
      >
        <Field
          label="Mã định danh độc giả"
          value={reader}
          onChange={(event) => setReader(event.target.value)}
          required
          placeholder="Chọn từ hồ sơ độc giả"
        />
        <p className="data-description">
          Ngày hết hạn do hệ thống xác định theo quy định đang áp dụng.
        </p>
        <MutationFeedback error={save.error} success={save.isSuccess}>
          {save.data && `Đã cấp thẻ ${save.data.card_no}. Hạn thẻ: ${save.data.expires_at}.`}
        </MutationFeedback>
        <div className="actions">
          <Button type="submit" disabled={save.isPending}>
            Xác nhận cấp thẻ
          </Button>
        </div>
      </form>
    </Panel>
  );
}
export default function Readers({ screen }: { screen: ScreenDefinition }) {
  if (screen.id === "FE03.01") return <ReaderList />;
  if (screen.id === "FE03.02") return <ReaderProfile />;
  if (screen.id === "FE03.04") return <IssueCard />;
  return <ReaderForm />;
}
