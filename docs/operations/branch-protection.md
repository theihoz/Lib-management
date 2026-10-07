# Bảo vệ nhánh main

## Trạng thái ngày 07/10/2026

Repository đã public. Đã bật và đọc lại thành công cả branch protection và ruleset
**Protect main — team workflow**, ID `24628362`, enforcement **Active**.
Ruleset: https://github.com/theihoz/Lib-management/rules/24628362

Trước khi repo public, GitHub Free/private đã trả HTTP403; hạn chế đó không còn
chặn cấu hình sau khi chủ repo đổi visibility. Lần xác nhận này đọc trạng thái
server, không chỉ dựa vào file JSON.

## Quy tắc đang áp dụng

- Thay đổi main qua PR, ít nhất 1 approval từ reviewer khác tác giả.
- Approval cũ bị bỏ khi push thêm commit; phải giải quyết review conversations.
- `ci-result` bắt buộc từ GitHub Actions (App ID `15368`); nhánh phải cập nhật main.
- Cấm force push và xóa main.
- Branch protection enforce cả admin; ruleset không có bypass actor.
- Không bắt buộc linear history; hỗ trợ merge/squash/rebase qua PR nếu đủ điều kiện.

Hai lớp bảo vệ chạy đồng thời. Không tắt một lớp để vượt điều kiện lớp còn lại.
Chủ repo có thể quản trị cấu hình; thao tác push/merge vẫn phải đáp ứng quy tắc.
Không tự approve PR của chính mình. Maintainer cần thêm thành viên có quyền review.

## Cấu hình trong Git

- [Branch protection](../../.github/branch-protection/main.json)
- [Ruleset](../../.github/rulesets/main.json)

Để cập nhật có chủ đích, dùng gh với quyền quản trị từ root repository:

```bash
gh api --method PUT repos/theihoz/Lib-management/branches/main/protection --input .github/branch-protection/main.json
gh api --method PUT repos/theihoz/Lib-management/rulesets/24628362 --input .github/rulesets/main.json
gh api repos/theihoz/Lib-management/branches/main/protection
gh api repos/theihoz/Lib-management/rulesets/24628362
```

Payload ruleset dùng PUT ID hiện có; không POST để tránh tạo rule trùng.
Rule chỉ nhắm `refs/heads/main`, không khóa các feature branch. Environment
`image-publish` là thiết lập khác và chưa được xác nhận trong nhiệm vụ này.
