import os
import sys
import time
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

# Force UTF-8 console output for Windows terminal compatibility
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

def main():
    output_path = r"C:\Users\Admin\Desktop\extracted_links.txt"
    shop_url = "https://shopee.vn/byjane.hn#product_list"
    
    print("🌐 Connecting to Chrome via CDP on port 9222...")
    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
            context = browser.contexts[0]
            # Try to find an existing shopee page first, or open a new one
            page = None
            for p_active in context.pages:
                if "shopee.vn" in p_active.url:
                    page = p_active
                    print(f"✅ Found active Shopee tab: {page.url}")
                    break
            
            if not page:
                page = context.new_page()
                print("✅ Opened new tab for Shopee.")
        except Exception as e:
            print("❌ Cannot connect to Chrome debug port 9222.")
            print("Please click the 'Mở Trình Duyệt Debug (Tự động)' button on the web app first, and log in to Shopee.")
            return

        print(f"📦 Loading shop page: {shop_url}")
        page.goto(shop_url, wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(3000)
        
        print("⏳ Incremental scrolling to load ALL products on the shop...")
        # Shopee has up to 100+ products per shop, scroll down incrementally
        for i in range(25):
            page.evaluate("window.scrollBy(0, 1000)")
            page.wait_for_timeout(800)
            if i % 5 == 0:
                print(f"  Scrolled step {i+1}/25...")
        
        # Scroll up and down slightly to trigger any missed lazy loads
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(500)
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1000)
        
        print("📝 Extracting all product links...")
        html_content = page.content()
        soup = BeautifulSoup(html_content, "html.parser")
        
        anchors = soup.find_all("a", class_=lambda c: c and "contents" in c)
        links = []
        for a in anchors:
            href = a.get("href")
            if href and ("-i." in href or "/product/" in href):
                if href.startswith("/"):
                    href = "https://shopee.vn" + href
                links.append(href)
                
        unique_links = []
        for l in links:
            if l not in unique_links:
                unique_links.append(l)
                
        # Save to Desktop
        with open(output_path, "w", encoding="utf-8") as f:
            for l in unique_links:
                f.write(l + "\n")
                
        # Save to project root too
        with open(r"c:\Users\Admin\model\extracted_links.txt", "w", encoding="utf-8") as f:
            for l in unique_links:
                f.write(l + "\n")
                
        print(f"Extraction completed successfully! Found a total of {len(unique_links)} products.")
        print(f"Saved directly to: {output_path}")

if __name__ == "__main__":
    main()
