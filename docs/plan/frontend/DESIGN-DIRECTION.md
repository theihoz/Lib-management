# Định hướng redesign frontend — Thư viện đương đại

**Trạng thái:** Đặc tả để triển khai, chưa có frontend runtime. **Ngày:** 2026-10-07.

## Mục đích, đối tượng và điểm nhận diện

Quầy nhân viên cần thao tác nhanh với bàn phím và máy quét; portal độc giả cần khám phá sách và biết việc cần làm tiếp theo trên mobile. Phong cách lấy cảm hứng từ bố cục ấn phẩm và mục lục thư viện: nền giấy sáng, đường phân cách mảnh, nhãn mục nhỏ, tiêu đề có chất sách và dữ liệu gọn.

Điểm nhận diện là **thanh hành trình mượn sách**: Xác định độc giả → Chọn sách → Xác nhận → Biên nhận. Thanh này nối với vùng điều kiện độc giả cố định trên quầy. Chuyển động đánh dấu bước vừa hoàn thành; không biến luồng tác nghiệp thành trình diễn.

Dùng tinh thần nhất quán của taste, không áp dụng hiệu ứng video, flash, particles hoặc motion theo nhạc vào ứng dụng. Quầy ưu tiên mật độ và sự ổn định; portal có không gian và bìa sách rõ hơn.

## Token giao diện

Đặc tả này tinh chỉnh phần trình bày đã ghi trong decisions.md; nghiệp vụ, actor và tên dữ liệu giữ nguyên. Các giá trị dưới đây là mục tiêu thiết kế, cần đo contrast khi triển khai; không coi là kết quả kiểm tra đã đạt.

| Token | Giá trị | Vai trò |
| --- | --- | --- |
| --canvas | #F7F5EF | Nền giấy ấm |
| --surface | #FFFFFF | Form/bảng/dialog |
| --ink | #17212B | Chữ chính |
| --muted | #53616B | Nhãn phụ |
| --primary | #174B73 | CTA và trạng thái chọn, giữ nhận diện DOCX |
| --accent | #9B4B2F | Điểm nhấn đất nung cho nhãn biên tập |
| --border | #D8DCD8 | Đường chia vùng |
| --success | #146C43 | Hoàn tất, kèm chữ/icon |
| --warning | #8A4B08 | Chờ duyệt/quá hạn |
| --danger | #B42318 | Lỗi/nguy cơ |
| --nav | #142C35 | Sidebar tối, chữ sáng |

- Body dùng Arial/system sans 16px; bảng nhân viên 14px, line-height 1.5; số tiền/mã/thời gian dùng tabular-nums. Tiêu đề trang dùng Georgia/serif có hỗ trợ tiếng Việt 28–36px; chỉ tiêu đề biên tập dùng serif, form và dữ liệu dùng sans.
- Spacing 4/8/12/16/24/32px; radius control 8px, panel 12px; dialog shadow nhẹ. Hạn chế bo tròn toàn bộ thành pill.
- Focus vòng 2px primary, offset 3px. Control tương tác ít nhất 44px; màu không là dấu hiệu duy nhất. Đo contrast chữ thường >=4.5:1.
- Không thêm font CDN, không tạo dependency chỉ để có hiệu ứng. Bìa dùng MediaAsset thực hoặc fallback có title/author; fallback không giả làm ảnh sách thật.

## Bố cục và responsive

| Vùng | Desktop >=1200px | Tablet 768–1199px | Mobile <768px |
| --- | --- | --- | --- |
| Quầy nhân viên | Sidebar 232px; vùng làm việc 2 cột; biên nhận 340px | Sidebar thành rail 72px hoặc drawer; 1 cột khi thiếu chỗ | Drawer; scan/form trước; tóm tắt theo luồng, không cố định che trường |
| Portal | Header gọn; catalog 4–5 cột; chi tiết sách 2 cột | Catalog 3 cột | Catalog 2 cột; ảnh 2:3; điều hướng bottom bar có safe-area |
| Dữ liệu | Toolbar ổn định; bảng có header, filter và pagination | Cuộn trong vùng bảng | Chuyển mục chính sang list; bảng phức tạp cuộn nội bộ có hướng dẫn |

Không có hero marketing trước công cụ. Trang nhân viên mở vào tác vụ theo quyền; portal mở catalog. Dùng page header, toolbar và vùng nội dung có đường chia thay vì card lồng card. Header sticky phải cộng offset khi focus/scroll; không che mục tiêu.

## Thành phần chủ đạo

- Navigation: marker cạnh trái cho mục đang chọn; icon quen thuộc kèm nhãn; route active rõ, không chỉ đổi màu.
- Page header: breadcrumb nhỏ, tiêu đề, một CTA chính; thao tác phụ thành nhóm hoặc menu rõ nhãn.
- Data table: số căn phải; row hover nhẹ; chọn dòng có checkbox/text; không biến cả row thành button nếu có nhiều action.
- Book tile: cover ratio 2:3, title tối đa 2 dòng, author và số bản khả dụng; click mở chi tiết, đặt trước là hành động riêng theo điều kiện.
- Reader strip: tên/mã/thẻ, điều kiện và các lý do; cảnh báo debt/pending assessment phân biệt. Update từ API không làm mất focus máy quét.
- Receipt: khối tóm tắt sạch, số phiếu nổi bật, chi tiết sách và hạn; in không có motion, navigation hay shadow.
- Confirmation dialog: tên action, đối tượng, tác động và lý do; focus trap, Escape đóng khi an toàn, trả focus về trigger.

## Trạng thái và chất lượng

Loading có placeholder đúng kích thước; empty có hướng hành động cụ thể; error cạnh trường/vùng dữ liệu; pending giữ layout và disable action lặp. Thành công có biên nhận hoặc kết quả bền vững, không chỉ toast. Conflict giữ input để người dùng sửa. Không dùng animation để giả tiến độ backend.

Nghiệm thu dự kiến: text tiếng Việt dài/zoom200%; keyboard toàn luồng; desktop/tablet/mobile; reduced motion; bảng/ảnh không gây layout shift; quyền bị thu hồi và API chậm. Kế hoạch chưa chứng minh các điều kiện này đã đạt.

## Triển khai theo PR

1. FE00.1: tokens và app shell; review hình tĩnh trước khi áp dụng toàn màn hình.
2. FE00.2: form/table/book tile/receipt, trạng thái và responsive.
3. FE00.3: motion primitives theo [MOTION.md](MOTION.md), không thêm thư viện animation trong giai đoạn này.
4. FE00.4: nghiệm thu accessibility, contrast, text fit và motion trên các luồng ưu tiên.

Đọc [mục lục frontend](README.md) để triển khai từng màn hình.
