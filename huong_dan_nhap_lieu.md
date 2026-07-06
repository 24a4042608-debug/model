# 📝 HƯỚNG DẪN NHẬP LIỆU SẢN PHẨM (MAPPING DATABASE & SHOP PRODUCT)

Tài liệu này hướng dẫn chi tiết cách ánh xạ (map) thông tin từ một trang chi tiết sản phẩm Shopee thực tế vào cơ sở dữ liệu hệ thống (Bảng `shop_products` / Model `RawProduct`) và cách điền vào biểu mẫu (form) nhập thủ công trên giao diện quản trị.

---

## 🗺️ BẢNG ÁNH XẠ DỮ LIỆU (DATABASE MAPPING TABLE)

Dưới đây là cách đối chiếu các trường dữ liệu giữa giao diện nhập liệu, mã nguồn database (`models.py`) và nội dung trang Shopee thực tế (sử dụng mẫu sản phẩm **Áo Khoác Cardigan BYJANE – 945** từ HTML bạn cung cấp):

| Tên trường trên Form UI | Cột Database (`RawProduct`) | Kiểu dữ liệu | Mô tả & Cách điền | Ví dụ thực tế từ mẫu BYJANE - 945 |
| :--- | :--- | :--- | :--- | :--- |
| **ID sản phẩm** | `product_id` | String(100) | Định danh duy nhất của sản phẩm. Bạn có thể tự đặt hoặc lấy từ URL Shopee. | `byjane_945` hoặc `145199886_43361044265` |
| **Tên sản phẩm** | `title` | Text | Tên hiển thị đầy đủ của sản phẩm. | `Áo Khoác Cardigan Nữ Dáng Dài Có Cúc Basic Thanh Lịch BYJANE – 945` |
| **Thương hiệu** | `brand` | String(100) | Tên hãng hoặc tên cửa hàng đăng bán. | `BYJANE` hoặc `BYJANE.HN` |
| **Giá bán (VNĐ)** | `price` | Decimal/Numeric | Giá bán dạng số để hệ thống tính toán (không nhập chữ hay dấu chấm). | `54000` (hoặc `108000`) |
| **Đường dẫn sản phẩm**| `url` | Text | Đường dẫn (link) gốc của sản phẩm trên Shopee. | `https://shopee.vn/product/145199886/43361044265` |
| **URL ảnh nổi bật** | `images` | JSON List | Đường dẫn trực tiếp của ảnh đại diện sản phẩm. | `https://down-vn.img.susercontent.com/file/vn-11134207-820l4-mj5xyaie7s3l0b` |
| **Danh mục** | `category` | Text | Chuỗi phân cấp danh mục sản phẩm từ ngoài vào trong. | `Thời Trang Nữ > Áo khoác, Áo choàng & Vest > Áo khoác ngoài` |
| **URL Video** | `video` | Text | Đường dẫn trực tiếp file video giới thiệu sản phẩm (.mp4). | `https://down-aka-vn.vod.susercontent.com/api/v4/11110105/mms/vn-11110105-6v8h1-mg4o0vr9a0wdba.16000081761108667.mp4` |
| **Đánh giá (Số sao)** | `rating_star` | Float/Double | Điểm đánh giá trung bình của sản phẩm (từ 0 đến 5.0). | `4.9` |
| **Số lượng đã bán** | `sold_count` | Integer | Tổng số lượng sản phẩm đã bán thành công. | `100000` (từ con số hiển thị `100k+`) |
| **Mô tả sản phẩm** | `description` | Text | Thông tin chi tiết về sản phẩm, chất liệu, size, hướng dẫn bảo quản. | *Xem chi tiết cách sao chép ở phần dưới.* |

---

## 🔍 HƯỚNG DẪN CHI TIẾT CÁCH TRÍCH XUẤT TỪ SHOPEE

Khi bạn muốn thêm một sản phẩm mới thủ công, hãy mở trang sản phẩm đó trên trình duyệt và lấy thông tin như sau:

### 1. Cách lấy ID sản phẩm (`product_id`)
* **Từ URL Shopee:** URL thường có dạng `.../product/{shop_id}/{item_id}`.
  * *Ví dụ:* Trong link `https://shopee.vn/product/145199886/43361044265`, `145199886` là Shop ID và `43361044265` là Item ID.
  * Bạn nên nhập ID sản phẩm là `{shop_id}_{item_id}` (ví dụ: `145199886_43361044265`) hoặc mã rút gọn của riêng bạn (ví dụ: `byjane_cardigan_945`).

### 2. Cách lấy Mô tả sản phẩm (`description`)
* Cuộn xuống phần **MÔ TẢ SẢN PHẨM** trên trang Shopee.
* Quét chuột bôi đen toàn bộ nội dung văn bản mô tả và copy.
* *Nội dung mẫu:*
  ```text
  🌟 ÁO CARDIGAN NỮ KHUY CÚC NHẸ NHÀNG, THANH LỊCH, DỄ PHỐI ĐỒ BYJANE 945 🌟
  Áo cardigan BYJANE thiết kế basic với hàng khuy cúc trước tinh tế...
  💥 THÔNG TIN SẢN PHẨM:
  ...
  ```

### 3. Cách lấy URL ảnh nổi bật (`images`)
* Nhấp chuột phải vào ảnh lớn của sản phẩm &rarr; chọn **Mở hình ảnh trong tab mới (Open image in new tab)**.
* Sao chép đường dẫn trên thanh địa chỉ. Đường dẫn ảnh Shopee chuẩn có dạng:
  `https://down-vn.img.susercontent.com/file/vn-...` hoặc `https://down-vn.img.susercontent.com/file/vn-..._tn`.

### 4. Cách lấy URL Video (`video`)
* Phát video giới thiệu sản phẩm trên trang Shopee.
* Nhấp chuột phải vào video &rarr; chọn **Sao chép địa chỉ video (Copy video address)** hoặc F12 xem thẻ `<video src="...">` để copy link. Đường dẫn có định dạng đuôi `.mp4`.
  * *Ví dụ:* `https://down-aka-vn.vod.susercontent.com/api/v4/11110105/mms/...mp4`

### 5. Cách lấy Danh mục (`category`)
* Nhìn vào thanh điều hướng bánh mì (Breadcrumbs) ở phía trên cùng của sản phẩm.
  * *Ví dụ:* `Shopee > Thời Trang Nữ > Áo khoác, Áo choàng & Vest > Áo khoác ngoài`.
  * Bạn copy chuỗi này và điền vào trường **Danh mục**.

---

## 🚀 CÁCH NHẬP LIỆU TRÊN GIAO DIỆN
1. Truy cập giao diện quản trị tại `http://localhost:5173`.
2. Mở tab đầu tiên **1. Sản phẩm**.
3. Nhấp vào nút **Thêm thủ công** ở phía trên bên phải của bảng danh sách.
4. Điền đầy đủ các thông tin vào các trường tương ứng dựa theo bảng ánh xạ ở trên.
5. Nhấp **Lưu thay đổi** để lưu sản phẩm vào cơ sở dữ liệu MySQL/SQLite.
