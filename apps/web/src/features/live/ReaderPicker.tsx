import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { useServices } from "../../auth/session";
import type { components } from "../../api/schema";
import { Button, Field, Notice, Table } from "../../ui/components";
import { MutationFeedback } from "./common";
import { recordStatus } from "./labels";

export type Reader = components["schemas"]["Reader"];

/** Find a reader by library card number first, then by reader code / name. */
export function ReaderPicker({ onPick }: { onPick: (reader: Reader) => void }) {
  const services = useServices();
  const [text, setText] = useState("");
  const search = useMutation({
    mutationFn: async (value: string) => {
      const byCard = (
        await services.readers.get_readers_lookup({ params: { query: { cardNo: value } } })
      ).data!.data;
      if (byCard.length) return byCard;
      return (await services.readers.get_readers_lookup({ params: { query: { query: value } } }))
        .data!.data;
    },
  });
  const rows = search.data ?? [];
  return (
    <>
      <form
        className="scan-form"
        onSubmit={(event) => {
          event.preventDefault();
          if (text.trim()) search.mutate(text.trim());
        }}
      >
        <Field
          label="Số thẻ, mã hoặc tên độc giả"
          required
          value={text}
          onChange={(event) => setText(event.target.value)}
        />
        <Button type="submit" variant="secondary" aria-busy={search.isPending}>
          Tìm độc giả
        </Button>
      </form>
      {search.error && <MutationFeedback error={search.error} />}
      {search.isSuccess && !rows.length && (
        <Notice tone="warning">Không tìm thấy độc giả phù hợp.</Notice>
      )}
      {rows.length > 0 && (
        <Table
          caption="Kết quả tìm độc giả"
          headers={["Mã độc giả", "Họ tên", "Trạng thái"]}
          rows={rows.map((row) => [row.reader_code, row.full_name, recordStatus(row.status)])}
          onRow={(index) => {
            const picked = rows[index];
            if (picked) onPick(picked);
          }}
        />
      )}
    </>
  );
}
