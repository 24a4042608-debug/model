"""
Shopee HTTP Crawler - Direct HTTP Request scraping using Googlebot headers and optional cookies.
Avoids starting a browser, bypassing resource overhead and CDP connection needs.
"""

import os
import re
import sys
import json
import time
import requests
from sqlalchemy.orm import Session

# Force UTF-8 console output for Windows terminal compatibility
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Import database models and repository
from automation.database.models import RawProduct, Product
from automation.database import repository
from automation.crawler.shopee_crawler import (
    extract_product_detail_with_soup,
    extract_product_links_with_soup,
    extract_sold_counts_from_shop,
    download_image,
    parse_username_from_shopee_url
)

# Standard Googlebot Headers representing Option 3
GOOGLEBOT_HEADERS = {
    'User-Agent': 'Googlebot/2.1 (+http://www.google.com/bot.html)',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Cache-Control': 'no-cache',
    'Pragma': 'no-cache',
    'Connection': 'keep-alive',
}

def crawl_product_http(url: str, db: Session, cookie: str = None, log_callback=None) -> dict:
    """Crawl a single product page using HTTP requests, with Googlebot headers and optional Cookie."""
    def log(msg: str):
        print(msg)
        if log_callback:
            log_callback(msg)

    log(f"⚡ [HTTP Crawler] Đang cào sản phẩm: {url}")
    
    headers = GOOGLEBOT_HEADERS.copy()
    # Use config cookie from env if parameter is missing
    if not cookie:
        cookie = os.getenv("SHOPEE_COOKIE", "")
        if cookie:
            log("🔑 Đang sử dụng Cookie mặc định cấu hình từ file .env.")

    if cookie:
        headers['Cookie'] = cookie
        log("🔑 Đang sử dụng Cookie cho phiên kết nối.")

    try:
        response = requests.get(url, headers=headers, timeout=20)
        
        if response.status_code != 200:
            log(f"❌ Yêu cầu thất bại. Mã trạng thái HTTP: {response.status_code}")
            return None
            
        # Detect if Shopee returned verify page (anti-bot)
        if "verify/traffic" in response.url or "captcha" in response.text.lower():
            log("❌ Shopee phát hiện Bot và chuyển hướng đến trang xác thực Captcha. Thử lại sau hoặc cập nhật Cookie mới.")
            return None

        html_content = response.text
        
        # Parse product details
        detail = extract_product_detail_with_soup(html_content)
        
        if not detail["title"]:
            log("⚠️ Không thể trích xuất tiêu đề sản phẩm (Có thể HTML thay đổi cấu trúc hoặc bị chặn).")
            return None

        # Extract product_id from URL
        match = re.search(r'[iI]\.(\d+)\.(\d+)', url)
        if not match:
            match = re.search(r'/product/(\d+)/(\d+)', url)
            
        if match:
            shop_id, item_id = match.group(1), match.group(2)
            product_id = f"{shop_id}_{item_id}"
        else:
            import hashlib
            product_id = hashlib.md5(url.encode()).hexdigest()

        # Check duplication
        existing = repository.get_raw_product_by_product_id(db, product_id)
        if existing:
            log(f"⏭️ Bỏ qua (Đã tồn tại trong DB): '{existing.title[:45]}...'")
            return detail

        # Download images
        local_images = []
        os.makedirs("public/images", exist_ok=True)
        for img_idx, img_url in enumerate(detail["images"][:10]):
            try:
                local_filename = f"{product_id}_{img_idx}.jpg"
                local_path = os.path.join("public", "images", local_filename)
                if download_image(img_url, local_path):
                    local_images.append(f"/images/{local_filename}")
            except Exception as img_err:
                log(f"  ⚠️ Lỗi tải ảnh: {img_err}")

        # Save to DB (raw_products)
        product_data = {
            "product_id": product_id,
            "title": detail["title"],
            "description": detail["description"],
            "price": detail["price"],
            "price_text": detail["price_text"],
            "brand": detail["details"].get("Thương hiệu", "BYJANE"),
            "category": detail["category"] or "Shopee",
            "details_json": json.dumps(detail["details"], ensure_ascii=False),
            "images": local_images,
            "video": detail["video"],
            "url": url,
            "rating_star": detail["rating_star"],
            "sold_count": detail["sold_count"]
        }
        repository.create_raw_product(db, product_data)
        
        # Save to main 'products' table
        username = parse_username_from_shopee_url(url) if "shopee.vn" in url else "shopee"
        main_product_data = {
            "keyword": username,
            "title": detail["title"],
            "price_text": detail["price_text"],
            "price_val": detail["price"],
            "rating_star": detail["rating_star"],
            "sold_count": detail["sold_count"],
            "image_url": detail["images"][0] if detail["images"] else "",
            "local_image_path": local_images[0] if local_images else "",
            "seo_keywords": "",
            "seo_description": "",
            "product_url": url
        }
        repository.create_product(db, main_product_data)

        log(f"✅ Đã thêm sản phẩm thành công: '{detail['title'][:45]}...'")
        return detail

    except Exception as e:
        log(f"❌ Lỗi khi cào sản phẩm: {e}")
        return None

def crawl_shop_http(shop_url: str, db: Session, cookie: str = None, max_products: int = 10, log_callback=None, check_stop_callback=None) -> int:
    """Crawl a shop's products using HTTP requests, with Googlebot headers and optional Cookie."""
    def log(msg: str):
        print(msg)
        if log_callback:
            log_callback(msg)

    username = parse_username_from_shopee_url(shop_url)
    log(f"⚡ [HTTP Shop Crawler] Bắt đầu quét shop: '{username}'")
    
    # Use config cookie from env if parameter is missing
    if not cookie:
        cookie = os.getenv("SHOPEE_COOKIE", "")
        if cookie:
            log("🔑 Đang sử dụng Cookie mặc định cấu hình từ file .env.")

    headers = GOOGLEBOT_HEADERS.copy()
    if cookie:
        headers['Cookie'] = cookie

    try:
        response = requests.get(shop_url, headers=headers, timeout=20)
        if response.status_code != 200:
            log(f"❌ Yêu cầu tải trang shop thất bại. Mã lỗi: {response.status_code}")
            return 0
            
        if "verify/traffic" in response.url:
            log("❌ Bị Shopee chặn xác thực (verify/traffic) trên trang shop. Vui lòng cập nhật Cookie.")
            return 0

        html_content = response.text
        
        # Extract product links
        links = extract_product_links_with_soup(html_content)
        shop_sold_counts = {}
        try:
            shop_sold_counts = extract_sold_counts_from_shop(html_content)
        except Exception as counts_err:
            log(f"⚠️ Không thể trích xuất số lượng đã bán từ danh sách: {counts_err}")
            
        valid_links = [l for l in links if '-i.' in l or '/product/' in l]
        log(f"✨ Tìm thấy {len(valid_links)} sản phẩm trên trang đầu.")

        if not valid_links:
            log("⚠️ Không tìm thấy sản phẩm nào trên trang cửa hàng này.")
            return 0

        if max_products > 0:
            valid_links = valid_links[:max_products]
            log(f"⚙️ Giới hạn cào: {max_products} sản phẩm.")

        total_added = 0
        log(f"📋 BẮT ĐẦU CRAWL CHI TIẾT {len(valid_links)} SẢN PHẨM")
        
        for idx, full_url in enumerate(valid_links, 1):
            if check_stop_callback and check_stop_callback():
                log("🛑 Tiến trình cào đã được dừng bởi người dùng.")
                break
                
            log(f"[{idx}/{len(valid_links)}] ━━━━━━━━━━━━━━━━━━━━")
            
            # Re-check duplication before fetching
            match = re.search(r'[iI]\.(\d+)\.(\d+)', full_url)
            if not match:
                match = re.search(r'/product/(\d+)/(\d+)', full_url)
            if match:
                product_id = f"{match.group(1)}_{match.group(2)}"
            else:
                import hashlib
                product_id = hashlib.md5(full_url.encode()).hexdigest()
                
            existing = repository.get_raw_product_by_product_id(db, product_id)
            if existing:
                log(f"  ⏭️ Bỏ qua (Đã tồn tại trong DB): '{existing.title[:45]}...'")
                continue

            # Crawl single product via HTTP
            detail = crawl_product_http(full_url, db, cookie=cookie, log_callback=log_callback)
            if detail:
                total_added += 1
                
            # Sleep to respect Shopee rate limiting
            time.sleep(5)

        log(f"\n🎉 [HTTP Shop Crawler] HOÀN THÀNH. Đã thêm mới: {total_added}/{len(valid_links)} sản phẩm.")
        return total_added

    except Exception as e:
        log(f"❌ Lỗi nghiêm trọng khi cào shop: {e}")
        return 0
