import { useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useServices, useSession } from "../../auth/session";
import { createIdempotencyKey } from "../../api/idempotency";
import type { components } from "../../api/schema";
import { formatDateTime } from "../../lib/datetime";
import { Button, Dialog, Field, Notice, Panel, Table } from "../../ui/components";
import { ApiFailure, LoadingSkeleton, MutationFeedback } from "./common";
import { reservationStatus } from "./labels";
import { ReaderPicker, type Reader } from "./ReaderPicker";
import {
  EditionPicker,
  PickedItem,
  editionAuthors,
  useLinkedEdition,
  type Edition,
} from "./EditionPicker";

type Row = components["schemas"]["Reservation"];

/** FE06.02 / BM04: reservations at the counter — hand over READY ones, cancel, reserve. */
export default function Reservations() {
  const services = useServices();
  const session = useSession();
  const cache = useQueryClient();
  const key = useRef(createIdempotencyKey()).current;
  const [target, setTarget] = useState<{ row: Row; action: "pickup" | "cancel" }>();
  const [reason, setReason] = useState("");
  const list = useQuery({
    queryKey: ["reservations", "active"],
    queryFn: async ({ signal }) =>
      (
        await services.circulation.get_reservations({
          params: { query: { status: "ACTIVE", limit: 100 } },
          signal,
        })
      ).data!.data,
    refetchInterval: 60_000,
  });
  const act = useMutation({
    mutationFn: async () => {
      const { row, action } = target!;
      const header = { "Idempotency-Key": key.forPayload({ id: row.id, action, reason }) };
      if (action === "pickup")
        return (
          await services.circulation.post_reservations_id_pickups({
            params: { path: { id: row.id }, header },
            body: { expectedVersion: row.version },
          })
        ).data!;
      return (
        await services.circulation.post_reservations_id_cancellations({
          params: { path: { id: row.id }, header },
          body: { expectedVersion: row.version, reason: reason.trim() || "Hủy tại quầy" },
        })
      ).data!;
    },
    onSuccess: () => {
      key.reset();
      setTarget(undefined);
      void cache.invalidateQueries({ queryKey: ["reservations"] });
    },
  });
  const rows = list.data ?? [];
  return (
    <div className="stack">
      <Panel title="Đặt trước đang hoạt động">
        {list.isPending ? (
          <LoadingSkeleton />
        ) : list.error ? (
          <ApiFailure error={list.error} retry={() => void list.refetch()} />
        ) : (
          <Table
            caption="Đặt trước đang hoạt động"
            headers={["Sách", "Trạng thái", "Ngày đặt", "Hạn nhận"]}
            rows={rows.map((row) => [
              row.title ?? row.edition_id,
              reservationStatus(row.status),
              formatDateTime(row.created_at),
              row.ready_expires_at ? formatDateTime(row.ready_expires_at) : "—",
            ])}
            onRow={(index) => {
              const row = rows[index];
              if (!row) return;
              setReason("");
              act.reset();
              setTarget({
                row,
                action:
                  row.status === "READY" && session.permissions.includes("reservation.pickup")
                    ? "pickup"
                    : "cancel",
              });
            }}
            empty={{ title: "Không có đặt trước", hint: "Chưa có độc giả nào đang chờ sách." }}
          />
        )}
        <p className="muted">
          Bấm tên sách: “Sẵn sàng nhận” để giao sách cho độc giả, còn lại để hủy. Giữ chỗ hết hạn
          sau số ngày quy định (C07) và tự chuyển cho người kế tiếp.
        </p>
        <MutationFeedback success={act.isSuccess}>Đã cập nhật đặt trước.</MutationFeedback>
      </Panel>
      {session.permissions.includes("reservation.create") && (
        <ReserveForReader
          onDone={() => void cache.invalidateQueries({ queryKey: ["reservations"] })}
        />
      )}
      <Dialog
        open={!!target}
        title={target?.action === "pickup" ? "Giao sách đặt trước" : "Hủy đặt trước"}
        pending={act.isPending}
        onClose={() => setTarget(undefined)}
      >
        <p>
          <strong>{target?.row.title}</strong> —{" "}
          {target ? reservationStatus(target.row.status) : ""}
        </p>
        {target?.action === "cancel" && (
          <Field
            label="Lý do hủy"
            maxLength={500}
            value={reason}
            onChange={(event) => setReason(event.target.value)}
          />
        )}
        {target?.action === "pickup" && (
          <Notice>Hệ thống lập phiếu mượn cho bản sách đang giữ chỗ.</Notice>
        )}
        <MutationFeedback error={act.error} />
        <div className="actions">
          <Button disabled={act.isPending} onClick={() => act.mutate()}>
            {target?.action === "pickup" ? "Giao sách" : "Xác nhận hủy"}
          </Button>
          {target?.action === "pickup" && (
            <Button
              variant="secondary"
              onClick={() => setTarget({ row: target.row, action: "cancel" })}
            >
              Hủy đặt trước
            </Button>
          )}
          <Button variant="secondary" onClick={() => setTarget(undefined)}>
            Quay lại
          </Button>
        </div>
      </Dialog>
    </div>
  );
}

function ReserveForReader({ onDone }: { onDone: () => void }) {
  const services = useServices();
  const key = useRef(createIdempotencyKey()).current;
  const [reader, setReader] = useState<Reader>();
  const linked = useLinkedEdition(new URLSearchParams(window.location.search).get("edition"));
  const [picked, setPicked] = useState<Edition | null>();
  const book = picked === undefined ? linked.data : (picked ?? undefined);
  const save = useMutation({
    mutationFn: async () => {
      const body = { readerId: reader!.id, editionId: book!.id };
      return (
        await services.circulation.post_reservations({
          body,
          params: { header: { "Idempotency-Key": key.forPayload(body) } },
        })
      ).data!;
    },
    onSuccess: () => {
      key.reset();
      onDone();
    },
  });
  return (
    <Panel title="Đặt trước cho độc giả">
      <div className="stack">
        {reader ? (
          <PickedItem
            label="Độc giả"
            title={reader.full_name}
            detail={reader.reader_code}
            onChange={() => setReader(undefined)}
          />
        ) : (
          <ReaderPicker onPick={setReader} />
        )}
        {book ? (
          <PickedItem
            label="Ấn bản"
            title={book.title}
            detail={`${editionAuthors(book)} · ${book.publication_year}`}
            onChange={() => setPicked(null)}
          />
        ) : (
          <EditionPicker onPick={setPicked} />
        )}
      </div>
      <form
        className="stack form-footer"
        onSubmit={(event) => {
          event.preventDefault();
          if (reader && book) save.mutate();
        }}
      >
        <Notice>
          Chỉ đặt được sách khi mọi bản đều đang được mượn. Tổng số sách đang mượn và đang đặt không
          vượt quá giới hạn theo quy định.
        </Notice>
        <MutationFeedback error={save.error} success={save.isSuccess}>
          Đã đặt trước; độc giả được báo khi sách sẵn sàng.
        </MutationFeedback>
        <Button type="submit" disabled={!reader || !book || save.isPending}>
          Đặt trước
        </Button>
      </form>
    </Panel>
  );
}
