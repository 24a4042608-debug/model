import sys
from playwright.sync_api import sync_playwright

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def main():
    print("🌐 Connecting to Chrome via CDP...")
    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
            context = browser.contexts[0]
            
            closed_count = 0
            for page in context.pages:
                url = page.url
                if "shopee.vn" in url and ("-i." in url or "/product/" in url):
                    print(f"Closing product tab: {url}")
                    page.close()
                    closed_count += 1
            print(f"✅ Closed {closed_count} product tabs.")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
