import os
import sys
import re
import json
import time
from playwright.sync_api import sync_playwright

# Adjust path to find automation package
sys.path.insert(0, "c:/Users/Admin/model")

from automation.database.models import SessionLocal, init_db
from automation.database import repository
from automation.crawler.shopee_crawler import extract_product_detail_with_soup, download_image, parse_username_from_shopee_url

# Force UTF-8 console output for Windows terminal compatibility
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

def crawl_single_product(page, url, db, username="shopee"):
    print(f"\n📥 Crawling details for: {url}")
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
        print(f"⏭️ Skipped (Already in DB): '{existing.title[:45]}...'")
        return True

    # Scroll down to trigger lazy loading of reviews and ratings
    page.evaluate("window.scrollBy(0, 500)")
    page.wait_for_timeout(1500)
    page.evaluate("window.scrollBy(0, 500)")
    page.wait_for_timeout(1500)

    # Parse details using BeautifulSoup
    html_content = page.content()
    detail = extract_product_detail_with_soup(html_content)

    if not detail["title"]:
        print("⏳ Title is empty. Waiting another 5 seconds...")
        page.wait_for_timeout(5000)
        detail = extract_product_detail_with_soup(page.content())

    if not detail["title"]:
        print("❌ Failed to parse product details (empty title).")
        return False

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
    print("🎉 Product successfully saved to database!")
    return True

def extract_product_links_from_shop(page):
    print("⏳ Scrolling open shop page to load all products...")
    # Scroll smoothly to load products
    for i in range(15):
        page.evaluate(f"window.scrollTo(0, {i * 800})")
        page.wait_for_timeout(1000)
    
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(500)

    from bs4 import BeautifulSoup
    html_content = page.content()
    soup = BeautifulSoup(html_content, 'html.parser')
    
    anchors = soup.find_all('a', class_=lambda c: c and 'contents' in c)
    if not anchors:
        anchors = soup.find_all('a', href=True)
        
    links = []
    for a in anchors:
        href = a.get('href')
        if href and ('-i.' in href or '/product/' in href):
            if href.startswith('/'):
                href = "https://shopee.vn" + href
            links.append(href)
            
    unique_links = []
    for link in links:
        if link not in unique_links:
            unique_links.append(link)
    return unique_links

def main():
    init_db()
    db = SessionLocal()

    print("🌐 Connecting to Chrome via CDP on port 9222...")
    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
            context = browser.contexts[0]
        except Exception as e:
            print(f"❌ Cannot connect to Chrome debug port 9222: {e}")
            print("👉 VUI LÒNG MỞ TRÌNH DUYỆT CHROME DEBUG TRƯỚC!")
            db.close()
            return

        # Find the Shopee page
        shopee_page = None
        for page in context.pages:
            if "shopee.vn" in page.url:
                shopee_page = page
                break

        if not shopee_page:
            print("❌ Không tìm thấy tab Shopee nào đang mở trên trình duyệt.")
            print("👉 Hãy mở Shopee (trang sản phẩm hoặc trang cửa hàng) trên trình duyệt Chrome debug rồi chạy lại tool.")
            db.close()
            return

        url = shopee_page.url
        print(f"✅ Found active Shopee tab: {url}")

        print("🔄 Activating and reloading tab to ensure dynamic content is loaded...")
        shopee_page.bring_to_front()
        try:
            shopee_page.reload(wait_until="domcontentloaded", timeout=45000)
        except Exception as reload_err:
            print(f"⚠️ Reload warning: {reload_err}")
        print("⏳ Waiting 6 seconds for page elements to render...")
        shopee_page.wait_for_timeout(6000)

        # Check page type
        is_product = "-i." in url or "/product/" in url
        if is_product:
            print("📝 Detected single product page. Starting crawl...")
            crawl_single_product(shopee_page, url, db)
        else:
            print("🛒 Detected shop/category page. Starting shop crawl...")
            username = parse_username_from_shopee_url(url)
            
            # Extract links
            links = extract_product_links_from_shop(shopee_page)
            print(f"✨ Found {len(links)} product links on the current page.")
            
            if not links:
                print("⚠️ Không tìm thấy liên kết sản phẩm nào. Hãy cuộn xuống để hiển thị sản phẩm.")
                db.close()
                return

            # Save links to desktop and workspace
            desktop_path = r"C:\Users\Admin\Desktop\extracted_links.txt"
            local_path = r"c:\Users\Admin\model\extracted_links.txt"
            
            with open(local_path, "w", encoding="utf-8") as f:
                for l in links:
                    f.write(l + "\n")
            with open(desktop_path, "w", encoding="utf-8") as f:
                for l in links:
                    f.write(l + "\n")
            print(f"💾 Saved product links to:\n  - {local_path}\n  - {desktop_path}")

            # Ask user if they want to crawl details now
            print(f"\n🚀 Starting to crawl detail for {len(links)} products...")
            detail_tab = context.new_page()
            total_added = 0
            
            for idx, link in enumerate(links, 1):
                print(f"\n[{idx}/{len(links)}] Loading page...")
                try:
                    detail_tab.goto(link, wait_until="domcontentloaded", timeout=30000)
                    detail_tab.wait_for_timeout(3000)
                    
                    # Scroll down to trigger lazy loading of reviews and ratings
                    detail_tab.evaluate("window.scrollBy(0, 500)")
                    detail_tab.wait_for_timeout(1500)
                    detail_tab.evaluate("window.scrollBy(0, 500)")
                    detail_tab.wait_for_timeout(1500)
                    
                    # Check anti-bot block
                    actual_url = detail_tab.url
                    if "verify/traffic" in actual_url or "/error" in actual_url:
                        print("⚠️ Shopee anti-bot detected! Please solve captcha if prompt appears.")
                        detail_tab.wait_for_timeout(10000)
                        detail_tab.goto(link, wait_until="domcontentloaded", timeout=30000)
                        detail_tab.wait_for_timeout(4000)
                        if "verify/traffic" in detail_tab.url:
                            print("❌ Still blocked. Skipping.")
                            continue

                    success = crawl_single_product(detail_tab, link, db, username)
                    if success:
                        total_added += 1
                        
                    time.sleep(5) # rate limit
                except Exception as page_err:
                    print(f"❌ Error crawling product {link}: {page_err}")

            try:
                detail_tab.close()
            except:
                pass
            print(f"\n🏁 Finished crawling current shop tab. Added {total_added} products to DB.")

    db.close()

if __name__ == "__main__":
    main()
