import os
import sys
import re
import json
import time
from playwright.sync_api import sync_playwright

# Adjust path to find automation package
sys.path.insert(0, "c:/Users/Admin/model")

from automation.database.models import SessionLocal, init_db, RawProduct
from automation.database import repository
from automation.crawler.shopee_crawler import extract_product_detail_with_soup, download_image

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

def main():
    # Pick the first URL
    url = "https://shopee.vn/product/1514216378/28733253030"
    product_id = "1514216378_28733253030"
    
    print("====================================================")
    print(f"🧪 CHẠY THỬ MẪU 1 LẦN: CÀO SẢN PHẨM")
    print(f"🔗 URL: {url}")
    print("====================================================")
    
    init_db()
    db = SessionLocal()
    
    # Clear existing so we can re-crawl as sample
    try:
        db.query(RawProduct).filter(RawProduct.product_id == product_id).delete()
        db.commit()
        print("🗑️ Đã xóa sản phẩm mẫu cũ trong DB để cào mới...")
    except Exception as e:
        print(f"⚠️ Warning clearing old sample: {e}")

    print("🌐 Khởi động Chrome chế độ persistent (headed) để tránh chặn...")
    crawler_profile = os.path.join(
        os.environ.get("LOCALAPPDATA", os.environ.get("USERPROFILE", "C:\\Users\\Admin")), 
        "ShopeeAutoCrawler", "sample_profile"
    )
    os.makedirs(crawler_profile, exist_ok=True)
    
    with sync_playwright() as p:
        try:
            context = p.chromium.launch_persistent_context(
                crawler_profile,
                headless=False,
                channel="chrome",
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-first-run",
                    "--disable-default-apps",
                ],
                viewport={"width": 1280, "height": 720},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                ignore_default_args=["--enable-automation"],
            )
            page = context.pages[0] if context.pages else context.new_page()
            
            print("📥 Đang tải trang sản phẩm...")
            page.goto(url, wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(5000)
            
            # Scroll down to load details
            print("📜 Cuộn trang để tải dữ liệu dynamic...")
            page.evaluate("window.scrollBy(0, 500)")
            page.wait_for_timeout(2000)
            
            # Parse detail
            html_content = page.content()
            detail = extract_product_detail_with_soup(html_content)
            
            if not detail["title"]:
                print("❌ Không parse được tiêu đề (Có thể trang bị chặn hoặc chưa load xong).")
                print("👉 Chụp ảnh màn hình để kiểm tra...")
                page.screenshot(path="scratch/sample_error.png")
                print("📸 Đã lưu ảnh chụp màn hình tại scratch/sample_error.png")
            else:
                print(f"✅ Cào thành công!")
                print(f"   - Tiêu đề: {detail['title']}")
                print(f"   - Giá: {detail['price_text']} ({detail['price']})")
                print(f"   - Đánh giá: {detail['rating_star']}⭐")
                print(f"   - Đã bán: {detail['sold_count']}")
                print(f"   - Danh mục: {detail['category']}")
                
                # Save to DB
                product_data = {
                    "product_id": product_id,
                    "title": detail["title"],
                    "description": detail["description"],
                    "price": detail["price"],
                    "price_text": detail["price_text"],
                    "brand": detail["details"].get("Thương hiệu", "BYJANE"),
                    "category": detail["category"] or "Shopee",
                    "details_json": json.dumps(detail["details"], ensure_ascii=False),
                    "images": [],
                    "video": detail["video"],
                    "url": url,
                    "rating_star": detail["rating_star"],
                    "sold_count": detail["sold_count"]
                }
                repository.create_raw_product(db, product_data)
                print("💾 Đã lưu sản phẩm vào cơ sở dữ liệu SQLite!")
                
        except Exception as e:
            print(f"❌ Lỗi trong quá trình cào: {e}")
        finally:
            db.close()

if __name__ == "__main__":
    main()
