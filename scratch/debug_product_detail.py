import sys
import re
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

# Force UTF-8 console output for Windows terminal compatibility
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

def main():
    url = "https://shopee.vn/(-KO-MÚT-KÈM-MÚT-)-Áo-ba-lỗ-nữ-cotton-mát-BYJANE-Áo-2-dây-bản-to-Áo-tanktop-co-dãn-4-chiều-phù-hợp-đi-tập-012-i.1514216378.28883412257"
    print("🌐 Connecting to Chrome via CDP on port 9222...")
    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
            context = browser.contexts[0]
            
            print(f"Opening product page: {url}")
            page = context.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=45000)
            print("Waiting 8 seconds for page to render fully...")
            page.wait_for_timeout(8000)
            
            # Take screenshot to verify it loaded
            screenshot_path = "scratch/product_detail_debug.png"
            page.screenshot(path=screenshot_path)
            print(f"Screenshot saved to {screenshot_path}")
            
            html = page.content()
            soup = BeautifulSoup(html, 'html.parser')
            
            # Save HTML to a debug file
            with open("scratch/product_page.html", "w", encoding="utf-8") as f:
                f.write(html)
            
            h1 = soup.find('h1')
            # Write results to a file
            with open("scratch/debug_results.txt", "w", encoding="utf-8") as out:
                out.write(f"Title h1 found: {h1.get_text(strip=True) if h1 else 'None'}\n\n")
                
                # Let's print out the text of any element that contains ₫
                price_els = []
                for tag in soup.find_all(text=re.compile('₫')):
                    price_els.append(tag.strip())
                out.write(f"Elements containing ₫ ({len(price_els)}):\n")
                for p in price_els[:20]:
                    out.write(f"  - {p}\n")
                out.write("\n")
                
                # Let's search for rating
                rating_matches = []
                for tag in soup.find_all(text=re.compile(r'^\d+\.\d+$')):
                    rating_matches.append(tag.strip())
                out.write("Elements matching decimal rating pattern:\n")
                for r in rating_matches[:20]:
                    out.write(f"  - {r}\n")
                out.write("\n")
                
                # Let's search for 'đã bán' or 'sold'
                sold_matches = []
                for tag in soup.find_all(text=re.compile(r'(đã bán|sold)', re.IGNORECASE)):
                    sold_matches.append(tag.parent.get_text(strip=True) if tag.parent else tag.strip())
                out.write("Elements containing 'đã bán' or 'sold':\n")
                for s in sold_matches[:20]:
                    out.write(f"  - {s}\n")
                out.write("\n")
                
                # Let's check the description
                desc_matches = []
                for tag in soup.find_all(text=re.compile(r'Mô tả sản phẩm', re.IGNORECASE)):
                    desc_matches.append(tag.parent.get_text(strip=True) if tag.parent else tag.strip())
                out.write("Elements containing 'Mô tả sản phẩm':\n")
                for d in desc_matches[:20]:
                    out.write(f"  - {d}\n")
                out.write("\n")
                
                # Let's print a sample of text content to see if there's any text on the page
                out.write("First 1000 characters of page text:\n")
                out.write(soup.get_text()[:1000])

            print("✅ Results written to scratch/debug_results.txt")
            page.close()
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
