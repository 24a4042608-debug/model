import sys
import time
from playwright.sync_api import sync_playwright

# Force UTF-8 console output for Windows terminal compatibility
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

def main():
    print("🌐 Connecting to Chrome via CDP on port 9222...")
    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
            context = browser.contexts[0]
            shopee_page = None
            for page in context.pages:
                if "shopee.vn" in page.url:
                    shopee_page = page
                    break

            if not shopee_page:
                print("❌ No Shopee page found.")
                return

            print(f"✅ Found Shopee page: {shopee_page.url}")
            print(f"Bringing tab to front and waiting...")
            shopee_page.bring_to_front()
            
            # Wait for content to load
            shopee_page.wait_for_timeout(5000)
            
            print(f"Title after wait: {shopee_page.title()}")
            print(f"URL after wait: {shopee_page.url}")
            
            html = shopee_page.content()
            print(f"HTML length: {len(html)}")
            
            # Check for selectors
            links = shopee_page.query_selector_all("a")
            print(f"Total 'a' tags via Playwright query: {len(links)}")
            
            # Let's count some divs
            divs = shopee_page.query_selector_all("div")
            print(f"Total 'div' tags via Playwright query: {len(divs)}")
            
            # Print first 5 links with text if any
            if links:
                print("First 10 links:")
                count = 0
                for link in links:
                    href = link.get_attribute("href")
                    text = link.inner_text().strip()
                    if href:
                        print(f"  href: {href} | text: {text[:50]}")
                        count += 1
                        if count >= 10:
                            break
            
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
