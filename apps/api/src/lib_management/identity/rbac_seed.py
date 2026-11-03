"""Single source of permission codes and default role grants.

Roles follow docs/design/permission-matrix.md (decision 03/11/2026): staff roles
are cumulative by name. Thủ thư runs the counter, Quản lý has everything a
Thủ thư has plus approvals, reports and policy, Admin hệ thống has every
permission; Admin vận hành keeps operations plus read-only reporting; Độc giả
only reaches their own data. Seeding never removes extra grants.
"""

PERMISSIONS: dict[str, str] = {
    "catalog.read": "Xem danh mục công khai",
    "catalog.write": "Tạo/sửa đầu sách, ấn bản, bản sao, phân loại",
    "media.write": "Tải/sửa ảnh bìa",
    "reader.read": "Xem hồ sơ độc giả",
    "reader.write": "Tạo/sửa hồ sơ độc giả",
    "card.issue": "Cấp/khóa/thu hồi thẻ thư viện",
    "eligibility.read": "Xem điều kiện mượn",
    "loan.checkout": "Cho mượn",
    "return.create": "Nhận trả",
    "loan.renew": "Gia hạn",
    "reservation.read": "Xem đặt trước",
    "reservation.create": "Tạo đặt trước",
    "reservation.cancel": "Hủy đặt trước",
    "reservation.pickup": "Giao sách đặt trước",
    "finance.read": "Xem dư nợ và lịch sử tài chính",
    "assessment.propose": "Đề xuất phí hỏng/mất",
    "payment.collect": "Thu tiền",
    "assessment.decide": "Duyệt phí hỏng/mất",
    "charge.waive": "Miễn phí",
    "ledger.reverse": "Đảo bút toán",
    "report.read": "Xem báo cáo",
    "overdue.read": "Xem danh sách quá hạn",
    "export.create": "Tạo tệp xuất CSV",
    "export.download": "Tải tệp xuất CSV",
    "policy.write": "Soạn quy định",
    "policy.approve": "Duyệt quy định",
    "account.provision_reader": "Cấp tài khoản độc giả",
    "account.manage": "Quản trị tài khoản",
    "role.manage": "Quản trị vai trò và quyền",
    "acquisition.write": "Lập phiếu nhập",
    "acquisition.approve": "Duyệt phiếu nhập",
    "copy.dispose": "Thanh lý bản sao",
    "backup.create": "Tạo bản sao lưu",
    "restore.request": "Yêu cầu khôi phục",
    "restore.approve": "Duyệt khôi phục",
    "job.read": "Xem tác vụ nền",
    "job.replay": "Chạy lại tác vụ nền",
    "notification.read": "Xem thông báo",
    "preference.write": "Đổi tùy chọn nhận thông báo",
}

_READER = (
    "catalog.read",
    "reader.read",
    "eligibility.read",
    "reservation.read",
    "reservation.create",
    "reservation.cancel",
    "finance.read",
    "notification.read",
    "preference.write",
)
_LIBRARIAN = (
    "catalog.read",
    "catalog.write",
    "media.write",
    "reader.read",
    "reader.write",
    "card.issue",
    "eligibility.read",
    "loan.checkout",
    "return.create",
    "loan.renew",
    "reservation.read",
    "reservation.create",
    "reservation.cancel",
    "reservation.pickup",
    "finance.read",
    "assessment.propose",
    "payment.collect",
    "report.read",
    "overdue.read",
    "account.provision_reader",
    "acquisition.write",
)
_MANAGER = (
    *_LIBRARIAN,
    "assessment.decide",
    "charge.waive",
    "ledger.reverse",
    "export.create",
    "export.download",
    "policy.write",
    "policy.approve",
    "acquisition.approve",
    "copy.dispose",
    "job.read",
)
_OPS_ADMIN = (
    "catalog.read",
    "report.read",
    "export.create",
    "export.download",
    "backup.create",
    "restore.request",
    "restore.approve",
    "job.read",
    "job.replay",
)

ROLES: dict[str, tuple[str, tuple[str, ...]]] = {
    "READER": ("Độc giả", _READER),
    "LIBRARIAN": ("Thủ thư", _LIBRARIAN),
    "MANAGER": ("Quản lý", _MANAGER),
    "SYSTEM_ADMIN": ("Admin hệ thống", tuple(PERMISSIONS)),
    "OPS_ADMIN": ("Admin vận hành", _OPS_ADMIN),
}
