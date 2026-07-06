import os
import sys
import re
import json
import time
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

# Adjust path to find automation package
sys.path.insert(0, "c:/Users/Admin/model")

from automation.database.models import SessionLocal, init_db, RawProduct, Product
from automation.database import repository
from automation.crawler.shopee_crawler import extract_product_detail_with_soup, download_image

# Force UTF-8 console output for Windows terminal compatibility
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

def main():
    links_file = r"c:\Users\Admin\model\extracted_links.txt"
    if not os.path.exists(links_file):
        print(f"❌ File {links_file} not found.")
        return
        
    with open(links_file, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip()]
        
    print(f"📖 Found {len(urls)} URLs in {links_file}.")
    
    init_db()
    db = SessionLocal()
    
    # Filter out already existing products
    urls_to_crawl = []
    for url in urls:
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
            
        existing = repository.get_raw_product_by_product_id(db, product_id)
        if not existing:
            urls_to_crawl.append((url, product_id))
        else:
            print(f"⏭️ Skipped (Already in DB): {url[:60]}...")
            
    print(f"🚀 Need to crawl details for {len(urls_to_crawl)} new products.")
    if not urls_to_crawl:
        print("✅ All products are already crawled!")
        db.close()
        return

    print("🌐 Connecting to Chrome via CDP on port 9222...")
    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
            context = browser.contexts[0]
            page = context.new_page()
            print("✅ Successfully connected to running Chrome instance!")
        except Exception as e:
            print(f"⚠️ CDP connection failed: {e}")
            print("🔄 Launching Chrome directly using persistent profile...")
            crawler_profile = os.path.join(
                os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), 
                "ShopeeAutoCrawler", "chrome_debug_profile"
            )
            os.makedirs(crawler_profile, exist_ok=True)
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
                print("✅ Successfully launched persistent Chrome browser!")
            except Exception as e2:
                print(f"❌ Failed to launch Chrome: {e2}")
                db.close()
                return
            
        consecutive_blocks = 0
        total_added = 0
        
        for idx, (url, product_id) in enumerate(urls_to_crawl, 1):
            print(f"\n[{idx}/{len(urls_to_crawl)}] Crawling: {url[:80]}...")
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                # Wait for SPA load
                page.wait_for_timeout(4000)
                
                # Check for anti-bot / captcha
                actual_url = page.url
                if "verify/traffic" in actual_url or "/error" in actual_url:
                    consecutive_blocks += 1
                    print(f"⚠️ Shopee anti-bot detected! (Attempts: {consecutive_blocks})")
                    print("👉 VUI LÒNG KIỂM TRA TRÌNH DUYỆT CHROME ĐANG MỞ VÀ GIẢI CAPTCHA NẾU CÓ!")
                    # Wait for user input or captcha solve
                    page.wait_for_timeout(20000)
                    # Retry
                    page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    page.wait_for_timeout(4000)
                    actual_url = page.url
                    if "verify/traffic" in actual_url or "/error" in actual_url:
                        print("❌ Still blocked. Skipping this product.")
                        continue
                        
                consecutive_blocks = 0
                
                # Scroll a bit to load reviews, images
                page.evaluate("window.scrollBy(0, 400)")
                page.wait_for_timeout(1000)
                
                # Parse detail
                html_content = page.content()
                detail = extract_product_detail_with_soup(html_content)
                
                if not detail["title"]:
                    print("⚠️ Title is empty. Waiting another 5 seconds...")
                    page.wait_for_timeout(5000)
                    detail = extract_product_detail_with_soup(page.content())
                    
                if not detail["title"]:
                    print("❌ Failed to parse product details (empty title). Skipping.")
                    continue
                    
                print(f"  ✅ Title: {detail['title']}")
                print(f"  💵 Price: {detail['price_text']} ({detail['price']})")
                print(f"  ⭐ Rating: {detail['rating_star']} | Sold: {detail['sold_count']}")
                
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
                        print(f"    ⚠️ Image download error: {img_err}")
                        
                # Create RawProduct
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
                
                # Create main Product
                main_product_data = {
                    "keyword": "byjane.hn",
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
                total_added += 1
                
                # Sleep between requests to avoid block
                time.sleep(5)
                
            except Exception as e:
                print(f"❌ Error crawling product: {e}")
                time.sleep(3)
                
        print(f"\n🏁 Finished. Added {total_added} products to DB.")
        db.close()

if __name__ == "__main__":
    main()
