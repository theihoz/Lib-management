import { useState } from "react";
import type { ReactNode } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useServices } from "../../auth/session";
import type { components } from "../../api/schema";
import { Button, Field, Notice, Table } from "../../ui/components";
import { MutationFeedback } from "./common";

export type Edition = components["schemas"]["PublicEdition"];

export const editionAuthors = (edition: Pick<Edition, "authors">) =>
  edition.authors?.map((author) => author.name).join(", ") || "Chưa có tác giả";

/** Find an edition by title, author or ISBN; never asks staff for an internal id. */
export function EditionPicker({ onPick }: { onPick: (edition: Edition) => void }) {
  const services = useServices();
  const [text, setText] = useState("");
  const search = useMutation({
    mutationFn: async (value: string) =>
      (
        await services.catalog.get_book_editions({
          params: { query: { query: value, limit: 10 } },
        })
      ).data!.data,
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
          label="Tên sách, tác giả hoặc ISBN"
          required
          value={text}
          onChange={(event) => setText(event.target.value)}
        />
        <Button type="submit" variant="secondary" aria-busy={search.isPending}>
          Tìm ấn bản
        </Button>
      </form>
      {search.error && <MutationFeedback error={search.error} />}
      {search.isSuccess && !rows.length && (
        <Notice tone="warning">Không tìm thấy ấn bản phù hợp.</Notice>
      )}
      {rows.length > 0 && (
        <Table
          caption="Kết quả tìm ấn bản"
          headers={["Nhan đề", "Tác giả", "Năm", "Khả dụng"]}
          rows={rows.map((row) => [
            row.title,
            editionAuthors(row),
            String(row.publication_year),
            String(row.availability?.availableCount ?? 0),
          ])}
          onRow={(index) => {
            const picked = rows[index];
            if (picked) onPick(picked);
          }}
        />
      )}
    </>
  );
}

/** Loads the edition named in a link such as `?edition=<id>` so the form shows its title. */
export function useLinkedEdition(id: string | null) {
  const services = useServices();
  return useQuery({
    queryKey: ["catalog", "edition", id],
    enabled: !!id,
    queryFn: async ({ signal }) =>
      (await services.catalog.get_book_editions_id({ params: { path: { id: id! } }, signal }))
        .data!,
  });
}

/** The chosen reader or edition, with a way to pick another one. */
export function PickedItem({
  label,
  title,
  detail,
  onChange,
}: {
  label: string;
  title: string;
  detail?: ReactNode;
  onChange: () => void;
}) {
  return (
    <div className="picked-item">
      <div>
        <span className="picked-label">{label}</span>
        <strong>{title}</strong>
        {detail && <span className="muted">{detail}</span>}
      </div>
      <Button variant="ghost" onClick={onChange}>
        Đổi
      </Button>
    </div>
  );
}
