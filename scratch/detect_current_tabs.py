import os
import sys
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
            pages = context.pages
            print(f"✅ Connected! Found {len(pages)} open tabs:")
            for idx, page in enumerate(pages, 1):
                try:
                    title = page.title()
                    url = page.url
                    print(f"  [{idx}] Title: {title}")
                    print(f"      URL: {url}")
                except Exception as page_err:
                    print(f"  [{idx}] Error reading tab: {page_err}")
        except Exception as e:
            print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    main()
