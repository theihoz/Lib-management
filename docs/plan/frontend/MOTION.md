# Motion frontend — Chuyển động để định hướng

**Trạng thái:** Đặc tả, chưa triển khai. **Ngày:** 2026-10-07.

## Nguyên tắc

Chuyển động làm rõ vị trí mới, item vừa thay đổi và kết quả thao tác. Quầy có nhịp nhanh; portal khám phá có nhịp nhẹ. Chỉ animation khi state/route/action đổi; không chạy hiệu ứng khi polling trả lại cùng dữ liệu. Người dùng có thể thao tác ngay trong transition.

Dùng CSS transitions/keyframes và Web Animations API khi cần điều phối. Không thêm thư viện chỉ cho fade/slide. Animate opacity/transform; tránh height/width/layout, blur toàn trang và background liên tục. Không dùng transition: all.

## Token motion

| Token | Mặc định | Mục đích |
| --- | --- | --- |
| --motion-fast | 120ms | Hover/focus/control |
| --motion-base | 180ms | Trạng thái hoặc item thêm |
| --motion-panel | 240ms | Drawer/dialog |
| --motion-page | 280ms | Portal page hoặc detail |
| --ease-out | cubic-bezier(.16,1,.3,1) | Xuất hiện/dịch chuyển tới đích |
| --ease-standard | cubic-bezier(.2,0,0,1) | Control/state |
| --ease-exit | cubic-bezier(.4,0,1,1) | Rời vùng; nhanh hơn vào |

Khoảng dịch tối đa 8px cho nội dung, 16px cho panel nhỏ; drawer bên cạnh dùng translateX ngoài viewport với backdrop opacity. Stagger portal 30ms mỗi mục, chỉ 6 mục đầu, tổng diễn tiến <=450ms. Quầy không stagger bảng hoặc danh sách quét.

## Bảng tương tác

| Tương tác | Trigger và chuyển động | Giới hạn/điều kiện |
| --- | --- | --- |
| Route nhân viên | Nội dung mới opacity0→1, y4→0 trong180ms | Shell không remount; không chờ exit mới thao tác; focus heading khi navigate bằng action |
| Route portal | opacity/y8 trong280ms | Không replay khi refetch hoặc back phục hồi vị trí |
| Navigation active | Marker dịch180ms hoặc highlight màu | Vị trí/label ổn định; reduced motion đổi tức thì |
| Button | Hover màu120ms; pressed translateY1px | Keyboard focus có vòng; disabled không hover motion |
| Book tile | Hover cover translateY−3px, shadow180ms | Chỉ thiết bị hover; không tilt theo chuột, không cắt nội dung |
| Search/filter | Kết quả mới crossfade120ms | Giữ vùng cao và focus search; debounce250ms cho text, hủy request cũ; không delay filter rõ |
| Thêm sách bằng scan | Dòng mới fade/y4 trong180ms, viền nhấn400ms một lần | Chỉ sau xác nhận server/lookup; announce một lần; không kéo focus khỏi scanner |
| Xóa mục khỏi phiếu nháp | Fade120ms rồi cập nhật danh sách | Không gửi lệnh nghiệp vụ ngầm; focus chuyển sang item kế hoặc scanner |
| Điều kiện độc giả | Chip/reason đổi màu120ms, không shake | Lý do chữ bền vững; aria-live polite, không đọc lặp khi poll |
| Dialog/drawer | Dialog opacity/scale.98→1 trong240ms; exit120ms | Focus trap/inert nền; không animate scale whole app |
| Job đang chạy | Spinner nhỏ hoặc progress thật | Không mô phỏng phần trăm nếu backend không có; label vẫn đọc được |
| Receipt thành công | Fade180ms, check icon xuất hiện một lần | Không confetti; receipt không tự biến mất; print motion off |
| Toast | opacity/y8 trong180ms | Không lấy focus; lỗi quan trọng còn inline; có dismiss và đủ thời gian đọc |
| Policy diff/approval | Highlight vùng đã đổi180ms | Giữ giá trị trước/sau, không đánh đồng save với approval |
| Notification đọc | Badge và màu đổi120ms | Không re-sort ngay gây nhảy item đang focus |

## Giảm chuyển động

Tôn trọng prefers-reduced-motion: reduce: bỏ translate/scale/stagger, route/dialog đổi tức thì; dùng chữ/icon tĩnh cho pending thay spinner/skeleton shimmer. Thông tin và feedback vẫn đầy đủ. Không có blinking, flash hoặc parallax. Motion đang chạy cần được hủy khi route unmount; cleanup listener/animation.

```css
:root {
  --motion-fast: 120ms;
  --motion-base: 180ms;
  --motion-panel: 240ms;
  --motion-page: 280ms;
  --ease-out: cubic-bezier(.16, 1, .3, 1);
}
@media (prefers-reduced-motion: reduce) {
  :root {
    --motion-fast: 0ms;
    --motion-base: 0ms;
    --motion-panel: 0ms;
    --motion-page: 0ms;
  }
  .motion-enter, .motion-stagger, .motion-cover { animation: none; transform: none; }
  .pending-spinner, .skeleton-shimmer { animation: none; }
}
```

Snippet là hướng dẫn triển khai, không phải CSS đã có. Các component dùng animation duration cứng phải có override hoặc không được tạo.

## Nghiệm thu dự kiến

- Trigger lặp, polling và retry không replay motion vô ích; không nhân event handler.
- Focus không mất khi row animate; quét liên tục không phải chờ transition hoàn tất.
- API chậm không khóa toàn trang; chỉ action tương ứng pending.
- Reduced motion đủ feedback; tab/dialog/route hoạt động bằng keyboard.
- Portal list lớn không animate tất cả node; không gây layout shift do cover/skeleton.
- Tiến độ job dùng dữ liệu thật; không hứa thành công trước response.
- Dùng DevTools khi triển khai để xác định animation không layout-thrash; ghi môi trường đo, không đặt kết luận hiệu năng khi chưa chạy.
