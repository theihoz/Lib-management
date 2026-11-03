import type { ScreenDefinition } from "../features/types";

// Metadata derived from docs/libmanagement-figma/screens.json; fixture values are development-only.
export const screens: ScreenDefinition[] = [
  {
    "group": "01",
    "kind": "auth",
    "action": "Tiếp tục với SSO",
    "id": "FE01.01",
    "title": "Đăng nhập thư viện",
    "path": "/login",
    "implemented": true
  },
  {
    "group": "01",
    "kind": "auth",
    "action": "Chờ xác minh",
    "id": "FE01.02",
    "title": "Đang xác minh phiên",
    "path": "/session/checking",
    "implemented": true
  },
  {
    "group": "01",
    "kind": "auth",
    "action": "Đăng nhập lại",
    "id": "FE01.03",
    "title": "Phiên đăng nhập hết hạn",
    "path": "/session/expired",
    "implemented": true
  },
  {
    "group": "01",
    "kind": "auth",
    "action": "Về trang làm việc",
    "id": "FE01.04",
    "title": "Bạn chưa có quyền truy cập",
    "path": "/session/forbidden",
    "implemented": true
  },
  {
    "group": "01",
    "kind": "auth",
    "action": "Về danh mục sách",
    "id": "FE01.05",
    "title": "Tài khoản đã bị khóa",
    "path": "/session/inactive",
    "implemented": true
  },
  {
    "group": "01",
    "kind": "auth",
    "action": "Thử lại",
    "id": "FE01.06",
    "title": "Không thể kết nối",
    "path": "/session/offline",
    "implemented": true
  },
  {
    "group": "01",
    "kind": "auth",
    "action": "Xác nhận đăng xuất",
    "id": "FE01.07",
    "title": "Đăng xuất khỏi thư viện?",
    "path": "/logout",
    "implemented": true
  },
  {
    "group": "02",
    "kind": "catalog",
    "id": "FE02.01",
    "title": "Khám phá sách",
    "path": "/catalog",
    "implemented": false
  },
  {
    "group": "02",
    "kind": "book",
    "id": "FE02.02",
    "title": "Bến không chồng",
    "path": "/catalog/:editionId",
    "implemented": false
  },
  {
    "group": "02",
    "kind": "list",
    "headers": [
      "Mã",
      "Nhan đề",
      "Tác giả",
      "Năm",
      "Khả dụng"
    ],
    "action": "Thêm ấn bản",
    "id": "FE02.03",
    "title": "Danh mục ấn bản",
    "path": "/staff/catalog",
    "permission": "catalog.write",
    "implemented": false
  },
  {
    "group": "02",
    "kind": "form",
    "note": "Năm xuất bản từ năm hiện tại − 8 đến năm hiện tại, gồm cả hai biên.",
    "action": "Lưu ấn bản",
    "id": "FE02.04",
    "title": "Tạo / sửa ấn bản",
    "path": "/staff/catalog/editions/new",
    "fields": [
      "Nhan đề",
      "Tác giả",
      "Nhà xuất bản",
      "Năm xuất bản",
      "ISBN",
      "Thể loại"
    ],
    "permission": "catalog.write",
    "implemented": false
  },
  {
    "group": "02",
    "kind": "list",
    "headers": [
      "Barcode",
      "Ấn bản",
      "Tình trạng",
      "Lưu thông"
    ],
    "action": "Thêm bản sách",
    "id": "FE02.05",
    "title": "Bản sách và mã vạch",
    "path": "/staff/catalog/copies",
    "permission": "catalog.write",
    "implemented": false
  },
  {
    "group": "02",
    "kind": "list",
    "headers": [
      "Tác giả",
      "Giới thiệu",
      "Trạng thái"
    ],
    "action": "Thêm tác giả",
    "id": "FE02.06",
    "title": "Tác giả",
    "path": "/staff/catalog/authors",
    "fields": [
      "Tên tác giả",
      "Giới thiệu"
    ],
    "permission": "catalog.write",
    "implemented": false
  },
  {
    "group": "02",
    "kind": "list",
    "headers": [
      "Tên nhà xuất bản",
      "Địa chỉ",
      "Trạng thái"
    ],
    "action": "Thêm nhà xuất bản",
    "id": "FE02.07",
    "title": "Nhà xuất bản",
    "path": "/staff/catalog/publishers",
    "fields": [
      "Tên nhà xuất bản",
      "Địa chỉ"
    ],
    "permission": "catalog.write",
    "implemented": false
  },
  {
    "group": "02",
    "kind": "tree",
    "id": "FE02.08",
    "title": "Phân loại sách",
    "path": "/staff/catalog/categories",
    "permission": "catalog.write",
    "implemented": false
  },
  {
    "group": "02",
    "kind": "upload",
    "id": "FE02.09",
    "title": "Ảnh bìa ấn bản",
    "path": "/staff/catalog/covers",
    "permission": "catalog.write",
    "implemented": false
  },
  {
    "group": "03",
    "kind": "list",
    "headers": [
      "Mã độc giả",
      "Họ tên",
      "Thẻ",
      "Dư nợ",
      "Điều kiện"
    ],
    "action": "Thêm độc giả",
    "id": "FE03.01",
    "title": "Độc giả và thẻ",
    "path": "/staff/readers",
    "permission": "reader.read",
    "implemented": false
  },
  {
    "group": "03",
    "kind": "profile",
    "id": "FE03.02",
    "title": "Hồ sơ độc giả",
    "path": "/staff/readers/:readerId",
    "permission": "reader.read",
    "implemented": false
  },
  {
    "group": "03",
    "kind": "form",
    "action": "Lưu hồ sơ",
    "note": "Thông tin trong bản thiết kế là dữ liệu minh họa.",
    "id": "FE03.03",
    "title": "Tạo / sửa hồ sơ độc giả",
    "path": "/staff/readers/new",
    "fields": [
      "Họ tên",
      "Ngày sinh",
      "Email",
      "Điện thoại",
      "Địa chỉ",
      "Loại độc giả"
    ],
    "permission": "reader.read",
    "implemented": false
  },
  {
    "group": "03",
    "kind": "form",
    "action": "Xác nhận cấp thẻ",
    "note": "Ngày hết hạn lấy từ kết quả xem trước; không tự đặt thời hạn thẻ.",
    "id": "FE03.04",
    "title": "Cấp thẻ thư viện",
    "path": "/staff/readers/cards/new",
    "fields": [
      "Độc giả",
      "Ngày cấp",
      "Hạn thẻ",
      "Mã thẻ"
    ],
    "permission": "reader.read",
    "implemented": false
  },
  {
    "group": "03",
    "kind": "form",
    "action": "Xác nhận liên kết",
    "note": "Không cấp vai trò nhân viên hoặc quản trị tại luồng này. Có trạng thái trùng, chờ xử lý, thành công và lỗi.",
    "id": "FE03.05",
    "title": "Cấp / liên kết tài khoản",
    "path": "/staff/readers/accounts/link",
    "fields": [
      "Độc giả có sẵn",
      "Tên tài khoản",
      "Liên kết hiện tại",
      "Phương án"
    ],
    "permission": "reader.read",
    "implemented": false
  },
  {
    "group": "04",
    "kind": "checkout",
    "id": "FE04.01",
    "title": "Quầy mượn sách",
    "path": "/staff/checkout",
    "permission": "loan.checkout",
    "implemented": false
  },
  {
    "group": "04",
    "kind": "checkout",
    "blocked": true,
    "id": "FE04.02",
    "title": "Chưa đủ điều kiện mượn",
    "path": "/staff/checkout/ineligible",
    "permission": "loan.checkout",
    "implemented": false
  },
  {
    "group": "04",
    "kind": "checkout",
    "conflict": true,
    "id": "FE04.03",
    "title": "Bản sách không còn khả dụng",
    "path": "/staff/checkout/conflict",
    "permission": "loan.checkout",
    "implemented": false
  },
  {
    "group": "04",
    "kind": "list",
    "headers": [
      "Số phiếu",
      "Độc giả",
      "Ngày mượn",
      "Hạn trả",
      "Trạng thái"
    ],
    "action": "Lập phiếu mượn",
    "id": "FE04.04",
    "title": "Phiếu mượn",
    "path": "/staff/loans",
    "permission": "loan.checkout",
    "implemented": false
  },
  {
    "group": "04",
    "kind": "loan",
    "id": "FE04.05",
    "title": "Chi tiết phiếu PM-1024",
    "path": "/staff/loans/:loanId",
    "permission": "loan.checkout",
    "implemented": false
  },
  {
    "group": "05",
    "kind": "returns",
    "id": "FE05.01",
    "title": "Tiếp nhận trả sách",
    "path": "/staff/returns",
    "permission": "return.create",
    "implemented": false
  },
  {
    "group": "05",
    "kind": "returns",
    "condition": true,
    "id": "FE05.02",
    "title": "Đánh giá tình trạng sách",
    "path": "/staff/returns/condition",
    "permission": "return.create",
    "implemented": false
  },
  {
    "group": "05",
    "kind": "form",
    "action": "Ghi nhận trả & gửi đề xuất",
    "note": "Sách được nhận trả ngay. Đề xuất chưa phải dư nợ; Quản lý xác nhận số tiền hoặc kết thúc không thu.",
    "id": "FE05.03",
    "title": "Đề xuất phí hỏng / mất",
    "path": "/staff/returns/assessment",
    "fields": [
      "Khoản mượn",
      "Tình trạng",
      "Số tiền đề xuất",
      "Lý do bắt buộc"
    ],
    "permission": "return.create",
    "implemented": false
  },
  {
    "group": "05",
    "kind": "receipt",
    "note": "Khoản phí hỏng đang chờ Quản lý xác nhận. Thu tiền là thao tác riêng.",
    "id": "FE05.04",
    "title": "Biên nhận trả sách",
    "path": "/staff/returns/receipt",
    "permission": "return.create",
    "implemented": false
  },
  {
    "group": "06",
    "kind": "list",
    "headers": [
      "Mã đặt",
      "Độc giả",
      "Ấn bản",
      "Trạng thái",
      "Hạn nhận"
    ],
    "action": "Hỗ trợ đặt trước",
    "id": "FE06.01",
    "title": "Hàng đợi giữ chỗ",
    "path": "/staff/reservations",
    "permission": "loan.renew",
    "implemented": false
  },
  {
    "group": "06",
    "kind": "hold",
    "id": "FE06.02",
    "title": "Chi tiết đặt trước DC-207",
    "path": "/staff/reservations/:reservationId",
    "permission": "loan.renew",
    "implemented": false
  },
  {
    "group": "06",
    "kind": "hold",
    "expired": true,
    "id": "FE06.03",
    "title": "Nhận sách / hết hạn giữ chỗ",
    "path": "/staff/reservations/expired",
    "permission": "loan.renew",
    "implemented": false
  },
  {
    "group": "06",
    "kind": "renew",
    "id": "FE06.04",
    "title": "Xem trước gia hạn",
    "path": "/staff/renewals",
    "permission": "loan.renew",
    "implemented": false
  },
  {
    "group": "06",
    "kind": "receipt",
    "note": "Đã gia hạn toàn bộ khoản OPEN một lần. Không gia hạn từng phần.",
    "id": "FE06.05",
    "title": "Biên nhận gia hạn",
    "path": "/staff/renewals/receipt",
    "permission": "loan.renew",
    "implemented": false
  },
  {
    "group": "07",
    "kind": "finance",
    "id": "FE07.01",
    "title": "Sổ tài chính độc giả",
    "path": "/staff/finance",
    "permission": "finance.read",
    "implemented": false
  },
  {
    "group": "07",
    "kind": "payment",
    "id": "FE07.02",
    "title": "Thu tiền và phân bổ",
    "path": "/staff/finance/payments/new",
    "permission": "finance.read",
    "implemented": false
  },
  {
    "group": "07",
    "kind": "list",
    "headers": [
      "Mã đề xuất",
      "Độc giả",
      "Bản sách",
      "Đề xuất",
      "Trạng thái"
    ],
    "action": "Xem đề xuất",
    "id": "FE07.03",
    "title": "Phí chờ xác nhận",
    "path": "/manager/charge-assessments",
    "permission": "finance.read",
    "implemented": false
  },
  {
    "group": "07",
    "kind": "assessment",
    "id": "FE07.04",
    "title": "Xác nhận phí hỏng / mất",
    "path": "/manager/charge-assessments/:assessmentId",
    "permission": "finance.read",
    "implemented": false
  },
  {
    "group": "07",
    "kind": "form",
    "action": "Xem lại & xác nhận",
    "note": "Chỉ Quản lý có quyền. Lưu lịch sử trước/sau; không sửa hoặc xóa giao dịch cũ.",
    "id": "FE07.05",
    "title": "Miễn / đảo khoản ghi nhận",
    "path": "/manager/finance/adjustments",
    "fields": [
      "Khoản phí",
      "Số tiền còn phải thu",
      "Thao tác",
      "Lý do bắt buộc"
    ],
    "permission": "finance.read",
    "implemented": false
  },
  {
    "group": "07",
    "kind": "list",
    "headers": [
      "Thời điểm",
      "Người thực hiện",
      "Sự kiện",
      "Đối tượng",
      "Số tiền"
    ],
    "note": "Sổ ghi nhận chỉ thêm; không có thao tác xóa lịch sử.",
    "id": "FE07.06",
    "title": "Lịch sử tài chính",
    "path": "/staff/finance/history",
    "permission": "finance.read",
    "implemented": false
  },
  {
    "group": "08",
    "kind": "portal",
    "id": "FE08.01",
    "title": "Của tôi",
    "path": "/me",
    "permission": "session",
    "implemented": false
  },
  {
    "group": "08",
    "kind": "ownloans",
    "id": "FE08.02",
    "title": "Sách đang mượn",
    "path": "/me/loans",
    "permission": "session",
    "implemented": false
  },
  {
    "group": "08",
    "kind": "ownholds",
    "id": "FE08.03",
    "title": "Đặt trước của tôi",
    "path": "/me/reservations",
    "permission": "session",
    "implemented": false
  },
  {
    "group": "08",
    "kind": "history",
    "id": "FE08.04",
    "title": "Lịch sử mượn và thanh toán",
    "path": "/me/history",
    "permission": "session",
    "implemented": false
  },
  {
    "group": "08",
    "kind": "ownfinance",
    "id": "FE08.05",
    "title": "Tài chính của tôi",
    "path": "/me/fine-charges",
    "permission": "session",
    "implemented": false
  },
  {
    "group": "08",
    "kind": "ownprofile",
    "id": "FE08.06",
    "title": "Hồ sơ và thẻ của tôi",
    "path": "/me/profile",
    "permission": "session",
    "implemented": false
  },
  {
    "group": "08",
    "kind": "notifications",
    "id": "FE08.07",
    "title": "Thông báo của tôi",
    "path": "/me/notifications",
    "permission": "session",
    "implemented": false
  },
  {
    "group": "08",
    "kind": "preferences",
    "id": "FE08.08",
    "title": "Tùy chọn nhận email",
    "path": "/me/preferences",
    "permission": "session",
    "implemented": false
  },
  {
    "group": "09",
    "kind": "list",
    "headers": [
      "Phiếu mượn",
      "Độc giả",
      "Hạn trả",
      "Số cuốn",
      "Phí đã ghi"
    ],
    "note": "Bấm số phiếu hoặc độc giả để mở hồ sơ phục vụ xử lý.",
    "id": "FE09.01",
    "title": "Danh sách quá hạn",
    "path": "/staff/overdue",
    "permission": "report.read",
    "implemented": false
  },
  {
    "group": "09",
    "kind": "reports",
    "id": "FE09.02",
    "title": "Báo cáo quản lý",
    "path": "/manager/reports",
    "permission": "report.read",
    "implemented": false
  },
  {
    "group": "09",
    "kind": "reports",
    "detail": true,
    "id": "FE09.03",
    "title": "Chi tiết báo cáo mượn trả",
    "path": "/manager/reports/:reportId",
    "permission": "report.read",
    "implemented": false
  },
  {
    "group": "09",
    "kind": "list",
    "headers": [
      "Tác vụ",
      "Tệp",
      "Trạng thái",
      "Hết hạn",
      "Thao tác"
    ],
    "action": "Tạo yêu cầu CSV",
    "note": "Chỉ Quản lý được xuất CSV. Kiểm tra lại quyền trước tải; tệp hết hạn cần tạo lại.",
    "id": "FE09.04",
    "title": "Xuất báo cáo CSV",
    "path": "/manager/exports",
    "permission": "report.read",
    "implemented": false
  },
  {
    "group": "09",
    "kind": "list",
    "headers": [
      "Phiên bản",
      "Trạng thái",
      "Hiệu lực",
      "Người duyệt"
    ],
    "action": "Tạo bản nháp",
    "id": "FE09.05",
    "title": "Phiên bản quy định",
    "path": "/manager/policies",
    "permission": "report.read",
    "implemented": false
  },
  {
    "group": "09",
    "kind": "policy",
    "id": "FE09.06",
    "title": "Quy định — bản nháp và so sánh",
    "path": "/manager/policies/new",
    "permission": "report.read",
    "implemented": false
  },
  {
    "group": "10",
    "kind": "list",
    "headers": [
      "Tài khoản",
      "Độc giả liên kết",
      "Vai trò",
      "Trạng thái",
      "Thao tác"
    ],
    "action": "Cấp / liên kết tài khoản",
    "id": "FE10.01",
    "title": "Tài khoản hệ thống",
    "path": "/admin/accounts",
    "permission": "account.manage",
    "implemented": false
  },
  {
    "group": "10",
    "kind": "permissions",
    "id": "FE10.02",
    "title": "Vai trò và phân quyền",
    "path": "/admin/roles",
    "permission": "account.manage",
    "implemented": false
  },
  {
    "group": "10",
    "kind": "list",
    "headers": [
      "Số phiếu",
      "Ngày lập",
      "Người lập",
      "Số mục",
      "Trạng thái"
    ],
    "action": "Lập phiếu nhập",
    "id": "FE10.03",
    "title": "Phiếu nhập sách",
    "path": "/staff/acquisitions",
    "permission": "account.manage",
    "implemented": false
  },
  {
    "group": "10",
    "kind": "acquisition",
    "id": "FE10.04",
    "title": "Lập phiếu nhập nhiều ấn bản",
    "path": "/staff/acquisitions/new",
    "permission": "account.manage",
    "implemented": false
  },
  {
    "group": "10",
    "kind": "acquisition",
    "id": "FE10.05",
    "title": "Duyệt và ghi nhận nhập kho",
    "path": "/manager/acquisitions/:receiptId",
    "permission": "account.manage",
    "implemented": false
  },
  {
    "group": "10",
    "kind": "receipt",
    "note": "POSTED · Chỉ đọc. Người lập: Thủ thư A. Người duyệt: Quản lý B.",
    "id": "FE10.06",
    "title": "Biên nhận nhập kho",
    "path": "/staff/acquisitions/receipt",
    "permission": "account.manage",
    "implemented": false
  },
  {
    "group": "10",
    "kind": "list",
    "headers": [
      "Barcode",
      "Ấn bản",
      "Tình trạng",
      "Điều kiện",
      "Thao tác"
    ],
    "action": "Đề nghị thanh lý",
    "id": "FE10.07",
    "title": "Thanh lý bản sách",
    "path": "/staff/disposals",
    "permission": "account.manage",
    "implemented": false
  },
  {
    "group": "10",
    "kind": "form",
    "action": "Xác nhận thanh lý",
    "note": "Quản lý thực hiện theo quyền. Ghi lại lịch sử; chặn nếu đang mượn hoặc có giữ chỗ.",
    "id": "FE10.08",
    "title": "Xác nhận tác động thanh lý",
    "path": "/staff/disposals/confirm",
    "fields": [
      "Bản sách",
      "Kiểm tra khoản mượn",
      "Kiểm tra giữ chỗ",
      "Lý do bắt buộc"
    ],
    "permission": "account.manage",
    "implemented": false
  },
  {
    "group": "11",
    "kind": "list",
    "headers": [
      "Mã tác vụ",
      "Loại",
      "Trạng thái",
      "Lần thử",
      "Lần thử tiếp"
    ],
    "action": "Xem chi tiết",
    "id": "FE11.01",
    "title": "Tác vụ nền",
    "path": "/ops/jobs",
    "permission": "ops.job.read",
    "implemented": false
  },
  {
    "group": "11",
    "kind": "job",
    "id": "FE11.02",
    "title": "Chi tiết tác vụ JOB-119",
    "path": "/ops/jobs/:jobId",
    "permission": "ops.job.read",
    "implemented": false
  },
  {
    "group": "11",
    "kind": "list",
    "headers": [
      "Tác vụ",
      "Loại",
      "Lần thử",
      "Lỗi đã lọc",
      "Thao tác"
    ],
    "action": "Xem điều kiện chạy lại",
    "note": "Xác nhận trước replay; kiểm tra quyền và loại job cho phép. Không hiển thị secrets.",
    "id": "FE11.03",
    "title": "Tác vụ lỗi và chạy lại",
    "path": "/ops/jobs/failed",
    "permission": "ops.job.read",
    "implemented": false
  },
  {
    "group": "11",
    "kind": "list",
    "headers": [
      "Mã bản sao",
      "Thời điểm",
      "Kích thước",
      "Trạng thái",
      "Kiểm chứng"
    ],
    "action": "Tạo bản sao lưu",
    "id": "FE11.04",
    "title": "Sao lưu dữ liệu",
    "path": "/ops/backups",
    "permission": "ops.job.read",
    "implemented": false
  },
  {
    "group": "11",
    "kind": "backup",
    "id": "FE11.05",
    "title": "Chi tiết bản sao lưu",
    "path": "/ops/backups/:backupId",
    "permission": "ops.job.read",
    "implemented": false
  },
  {
    "group": "11",
    "kind": "form",
    "action": "Gửi đề nghị duyệt",
    "note": "Chỉ target cô lập trong allowlist. Không ghi đè hoặc tự chuyển sang DB đang phục vụ.",
    "id": "FE11.06",
    "title": "Yêu cầu khôi phục cô lập",
    "path": "/ops/restores/new",
    "fields": [
      "Bản sao lưu",
      "Target cho phép",
      "Checksum",
      "Lý do bắt buộc"
    ],
    "permission": "ops.job.read",
    "implemented": false
  },
  {
    "group": "11",
    "kind": "restore",
    "id": "FE11.07",
    "title": "Duyệt và kết quả khôi phục",
    "path": "/ops/restores/:restoreId",
    "permission": "ops.job.read",
    "implemented": false
  },
  {
    "group": "11",
    "kind": "list",
    "headers": [
      "Thời điểm",
      "Người thực hiện",
      "Hành động",
      "Đối tượng",
      "Kết quả"
    ],
    "id": "FE11.08",
    "title": "Nhật ký kiểm toán",
    "path": "/ops/audit",
    "permission": "ops.job.read",
    "implemented": false
  }
];

export const groups = [
  {
    "id": "01",
    "title": "Xác thực",
    "icon": "key"
  },
  {
    "id": "02",
    "title": "Danh mục",
    "icon": "book"
  },
  {
    "id": "03",
    "title": "Độc giả & thẻ",
    "icon": "users"
  },
  {
    "id": "04",
    "title": "Mượn sách",
    "icon": "scan"
  },
  {
    "id": "05",
    "title": "Trả sách",
    "icon": "return"
  },
  {
    "id": "06",
    "title": "Giữ chỗ & gia hạn",
    "icon": "clock"
  },
  {
    "id": "07",
    "title": "Tài chính",
    "icon": "wallet"
  },
  {
    "id": "08",
    "title": "Portal độc giả",
    "icon": "user"
  },
  {
    "id": "09",
    "title": "Báo cáo & quy định",
    "icon": "chart"
  },
  {
    "id": "10",
    "title": "Quản trị & kho",
    "icon": "archive"
  },
  {
    "id": "11",
    "title": "Vận hành",
    "icon": "settings"
  }
];
