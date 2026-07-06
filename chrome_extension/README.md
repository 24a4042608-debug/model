# Hướng dẫn sử dụng Chrome Extension: Shopee Automation Grabber 🔌

Extension này cho phép bạn cào dữ liệu trực tiếp từ trang web Shopee bằng cách mở trình duyệt thông thường của mình, bỏ qua hoàn toàn các lớp bảo vệ chống bot của Shopee (Anti-bot Captcha) vì nó chạy trực tiếp trên phiên trình duyệt thực của bạn.

---

## 🛠️ Hướng dẫn cài đặt

1. Mở trình duyệt Google Chrome (hoặc bất kỳ trình duyệt nhân Chromium nào như Edge, CocCoc, Brave).
2. Truy cập vào trang quản lý tiện ích bằng cách gõ địa chỉ: `chrome://extensions/` vào thanh địa chỉ.
3. Kích hoạt chế độ **Chế độ dành cho nhà phát triển (Developer mode)** ở góc trên bên phải màn hình.
4. Bấm vào nút **Tải tiện ích đã giải nén (Load unpacked)** ở góc trên bên trái.
5. Chọn thư mục `chrome_extension` nằm trong thư mục gốc của dự án này (`c:\Users\Admin\model\chrome_extension`).
6. Extension sẽ xuất hiện trong danh sách và sẵn sàng hoạt động! Bạn nên ghim (pin) biểu tượng Extension lên thanh công cụ để dễ dàng theo dõi.

---

## 🚀 Cách hoạt động

### 1. Cào trang sản phẩm đơn lẻ
- Khi bạn mở bất kỳ link sản phẩm Shopee nào (ví dụ: `https://shopee.vn/product/123/456...`), một khung thông báo nhỏ màu đen (HUD) sẽ xuất hiện ở **góc dưới bên phải màn hình**.
- Extension sẽ tự động trích xuất thông tin tiêu đề, mô tả, giá, hình ảnh, thông số kỹ thuật và gửi về Backend đang chạy tại `http://localhost:8000`.
- Nếu Backend đang hoạt động, HUD sẽ chuyển sang màu xanh lá: **"✅ Đã đồng bộ thành công!"** và sản phẩm sẽ xuất hiện ngay lập tức trên React Dashboard của bạn.

### 2. Cào trang cửa hàng/danh sách sản phẩm
- Khi bạn mở trang của một shop Shopee (ví dụ: `https://shopee.vn/shop-name`), HUD sẽ hiển thị nút **"⚡ Quét & Gửi sản phẩm Shop này"**.
- Bấm vào nút này, trang web sẽ tự động cuộn xuống để kích hoạt cơ chế tải lười (lazy load) của Shopee và gom toàn bộ danh sách liên kết sản phẩm.
- Sau khi quét xong, bạn chỉ cần bấm **"⚡ Gửi danh sách về Backend"**, Backend sẽ tự động chạy ngầm cào danh sách sản phẩm này thông qua HTTP Request crawler.

---

## ⚙️ Cấu hình địa chỉ Backend API
Mặc định Extension kết nối tới `http://localhost:8000`. Nếu backend của bạn chạy ở cổng khác:
1. Bấm vào biểu tượng Extension Shopee Grabber trên thanh công cụ.
2. Nhập URL backend mới tại ô **Backend API URL**.
3. Bấm **Lưu cấu hình**. Extension sẽ tự động kiểm tra kết nối và hiển thị kết quả.
