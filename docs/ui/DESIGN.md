# Thiết kế giao diện đề xuất

Bản đề xuất cho phần mềm quản lý thư viện; chưa có code giao diện để trích token hoặc chấm điểm một ứng dụng đã triển khai.

- Màu xanh đậm thể hiện hành động; trạng thái có chữ và biểu tượng, không phụ thuộc màu.
- Arial/system sans hỗ trợ tiếng Việt và môi trường quầy thư viện; body 16px, bảng 14px, không thu nhỏ chữ để nhồi dữ liệu.
- Khoảng cách 4/8/12/16/24/32px tạo nhịp thống nhất; vùng bấm tối thiểu 44px và focus rõ cho bàn phím/máy quét.
- Mượn và trả là hai luồng riêng; thu tiền là thao tác độc lập. UI hiển thị trạng thái đang xử lý, rỗng, lỗi và biên nhận khác nhau.
- Quầy mượn dùng ô quét thẻ, điều kiện và danh sách bản sao; preview hạn không thay việc kiểm tra lại trong transaction.
- Preview dùng dữ liệu minh họa, không gọi API hoặc ghi dữ liệu. Các nút chuyển màn hình và đổi trạng thái cho phép xem thiết kế.
- Contrast, keyboard, labels và responsive cần kiểm chứng khi triển khai. Không đưa điểm audit giả khi chưa có ứng dụng.

Tệp: `design-tokens.json`, `design-tokens.css`, `design-preview.html`. Phần 9 của tài liệu thiết kế ghi hợp đồng màn hình đầy đủ hơn.
