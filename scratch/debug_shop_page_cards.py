import sys
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import re

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

def main():
    print("🌐 Connecting to Chrome via CDP...")
    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
            context = browser.contexts[0]
            
            # Find the shop page
            shopee_page = None
            for page in context.pages:
                if "shopee.vn" in page.url and "-i." not in page.url and "/product/" not in page.url:
                    shopee_page = page
                    break
                    
            if not shopee_page:
                print("❌ Shop tab not found. Trying first shopee tab.")
                for page in context.pages:
                    if "shopee.vn" in page.url:
                        shopee_page = page
                        break
                        
            if not shopee_page:
                print("❌ No shopee tab found.")
                return
                
            print(f"✅ Found tab: {shopee_page.url}")
            shopee_page.bring_to_front()
            
            # Scroll down to load cards
            print("Scrolling...")
            shopee_page.evaluate("window.scrollTo(0, 1000)")
            shopee_page.wait_for_timeout(2000)
            
            html = shopee_page.content()
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find product cards
            # In Shopee, product cards are usually anchors containing details
            anchors = soup.find_all('a', href=True)
            print(f"Total anchors: {len(anchors)}")
            
            card_count = 0
            for idx, a in enumerate(anchors):
                href = a.get('href', '')
                if '-i.' in href or '/product/' in href:
                    card_count += 1
                    print(f"\nCard {card_count}:")
                    print(f"  Link: {href}")
                    
                    # Print all texts inside this anchor
                    text_parts = [t.strip() for t in a.find_all(text=True) if t.strip()]
                    print(f"  Texts: {text_parts}")
                    
                    # See if we can locate price and sold count
                    sold_part = None
                    price_part = None
                    for t in text_parts:
                        if 'bán' in t.lower() or 'sold' in t.lower():
                            sold_part = t
                        if '₫' in t or t.replace('.', '').isdigit():
                            price_part = t
                    print(f"  Detected Price: {price_part} | Sold: {sold_part}")
                    
                    if card_count >= 10:
                        break
                        
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
