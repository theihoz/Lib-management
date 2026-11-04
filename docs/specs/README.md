# Spec triển khai

Spec ở đây là bản đủ cụ thể để code một mốc: cấu trúc code, schema, hợp đồng HTTP, chia PR và tiêu chí nghiệm thu. Chúng tổng hợp từ [thiết kế](../design/README.md) và [kế hoạch](../plan/README.md), không thay thế các nguồn đó. Khi spec lệch nguồn chuẩn, sửa spec trong cùng PR.

Trạng thái: **Draft** (đang review) → **Approved** (team đồng ý, bắt đầu code) → **In review** (code đã có PR, chờ CI/merge) → **Implemented** (mọi PR đã merge, nghiệm thu có bằng chứng CI).

| Spec | Mốc | Task | Trạng thái |
| --- | --- | --- | --- |
| [M0 — Nền tảng backend, hợp đồng API và xác thực](M0-backend-foundation.md) | M0 | BE00, INT00.1/.3, BE01.1/.2 | In review |
| [M0 — Nền tảng frontend, client API và đăng nhập](M0-frontend-foundation.md) | M0 | FE00, FE01.1–.3, INT00.2 | Draft |

Phạm vi sản phẩm: lõi 10 tuần theo [quyết định 03/11/2026](../plan/decisions.md#quyết-định-03112026--phạm-vi-lõi-10-tuần).

[Spec hoàn thiện toàn bộ lõi 10 tuần](../superpowers/specs/2026-11-03-core-library-design.md) đã được người dùng duyệt03/11/2026; [kế hoạch thực thi](../superpowers/plans/2026-11-03-core-library.md). F14 thuộc lõi, D01 đã chốt; trạng thái triển khai được cập nhật theo từng mốc với bằng chứng.

[Quy định nguồn QĐ01–QĐ26](source-rules.md): bảng đối chiếu spec nhóm (Lab 2–4) với code và test, cập nhật 04/11/2026.

[Spec hoàn thiện phần còn thiếu 04/11/2026](../superpowers/specs/2026-11-04-spec-gap-completion.md) (Draft, chờ duyệt D1–D6) và [kế hoạch](../superpowers/plans/2026-11-04-spec-gap-completion.md): G1–G8 lõi, Q1–Q2 chất lượng, P1–P7 phase 2.
