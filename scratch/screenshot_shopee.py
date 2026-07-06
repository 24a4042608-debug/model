import sys
from playwright.sync_api import sync_playwright

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
            shopee_page.bring_to_front()
            
            print("🔄 Tab is sleeping/blank. Reloading tab to activate it...")
            shopee_page.reload(wait_until="domcontentloaded", timeout=45000)
            print("⏳ Waiting 6 seconds for dynamic SPA content to render...")
            shopee_page.wait_for_timeout(6000)
            
            screenshot_path = "scratch/shopee_page.png"
            shopee_page.screenshot(path=screenshot_path)
            print(f"✅ Screenshot saved to {screenshot_path}")
            
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
