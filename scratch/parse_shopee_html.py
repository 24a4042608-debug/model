import sys
import re
from bs4 import BeautifulSoup

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

def main():
    with open("scratch/product_page.html", "r", encoding="utf-8") as f:
        html = f.read()
        
    soup = BeautifulSoup(html, 'html.parser')
    
    with open("scratch/parse_results.txt", "w", encoding="utf-8") as out:
        out.write("=== DEBUG SHARPEST PARSING ===\n")
        
        # 1. Title
        h1 = soup.find('h1')
        out.write(f"Title: {h1.get_text(strip=True) if h1 else 'None'}\n\n")
        
        # 2. Price
        price_tags = []
        for el in soup.find_all(text=re.compile('₫')):
            p = el.parent
            price_tags.append(f"<{p.name} class='{p.get('class', [])}'>{p.get_text(strip=True)}</{p.name}>")
        out.write(f"Price tags ({len(price_tags)}):\n")
        for t in price_tags[:30]:
            out.write(f"   {t}\n")
        out.write("\n")
            
        # 3. Rating & Reviews
        rating_texts = []
        for el in soup.find_all(text=re.compile(r'\b(rating|đánh giá)\b', re.I)):
            rating_texts.append(el.parent.get_text(strip=True))
        out.write(f"Rating texts ({len(rating_texts)}):\n")
        for r in rating_texts[:20]:
            out.write(f"   {r}\n")
        out.write("\n")
            
        # Search for sold count text
        sold_texts = []
        for el in soup.find_all(text=re.compile(r'\b(sold|đã bán)\b', re.I)):
            sold_texts.append(el.parent.get_text(strip=True))
        out.write(f"Sold count texts ({len(sold_texts)}):\n")
        for s in sold_texts[:20]:
            out.write(f"   {s}\n")
        out.write("\n")
            
        # Let's search for the actual rating value (4.9)
        out.write("Finding elements with text '4.9':\n")
        for el in soup.find_all(text='4.9'):
            p = el.parent
            out.write(f"  <{p.name} class='{p.get('class', [])}'>{p.get_text(strip=True)}</{p.name}>\n")
        out.write("\n")

        # Let's search for "Description" or "Mô tả"
        desc_headers = []
        for el in soup.find_all(text=re.compile(r'(Description|Mô tả sản phẩm)', re.I)):
            desc_headers.append(el.parent.get_text(strip=True))
        out.write(f"Description headers ({len(desc_headers)}):\n")
        for d in desc_headers[:20]:
            out.write(f"   {d}\n")
        out.write("\n")
        
if __name__ == "__main__":
    main()
