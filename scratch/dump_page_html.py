import sys
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

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
            
            # Print a snippet of a tags
            html = shopee_page.content()
            print(f"HTML length: {len(html)}")
            print("HTML prefix:", html[:500])
            
            import re
            raw_hrefs = re.findall(r'href=["\']([^"\']+)["\']', html)
            print(f"Raw regex hrefs found: {len(raw_hrefs)}")
            for idx, href in enumerate(raw_hrefs[:20], 1):
                print(f"  Raw [{idx}]: {href}")
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find all anchors that might be products
            anchors = soup.find_all('a', href=True)
            print(f"Total anchor tags found: {len(anchors)}")
            
            shopee_links = []
            for a in anchors:
                href = a.get('href', '')
                if '-i.' in href or '/product/' in href or 'byjane.hn' in href:
                    shopee_links.append((href, a.get_text(strip=True)[:50]))
            
            print(f"Shopee-related links found ({len(shopee_links)}):")
            for idx, (href, text) in enumerate(shopee_links[:20], 1):
                print(f"  [{idx}] href: {href} | text: {text}")
                
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
