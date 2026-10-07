# Bảo vệ nhánh main

## Trạng thái ngày 07/10/2026

Repository private, tài khoản GitHub Free có quyền ADMIN. GitHub trả HTTP403:
“Upgrade to GitHub Pro or make this repository public to enable this feature.”
**Rule chưa được bật.** Không đổi repo sang public hoặc mua gói trong lượt này.

Payload ở [.github/branch-protection/main.json](../../.github/branch-protection/main.json):
PR có ít nhất 1 approval, dismiss approval cũ khi push thêm, `ci-result` bắt buộc,
nhánh phải cập nhật với main, resolve conversation, áp dụng cả admin; cấm force push
và xóa main. Reviewer phải là người khác tác giả PR; CI không thay thế review.

Sau khi chủ repo nâng gói hỗ trợ bảo vệ repo private, đăng nhập gh bằng tài khoản
quản trị và chạy từ repository root:

```bash
gh api --method PUT repos/theihoz/Lib-management/branches/main/protection --input .github/branch-protection/main.json
gh api repos/theihoz/Lib-management/branches/main/protection
```

Kiểm tra readback có `ci-result`, strict, approval_count1, enforce_admins,
conversation_resolution và force_push/deletions=false. JSON là cấu hình mong muốn,
không chứng minh GitHub đang cưỡng chế. Trong lúc chưa bật, team chỉ merge PR sau
review và CI thành công; đó là quy trình tự giác, chưa là rào chặn server.
