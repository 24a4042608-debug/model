import sys
import re

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

def main():
    try:
        with open("scratch/product_page.html", "r", encoding="utf-8") as f:
            html = f.read()
            
        print("Searching for 'sold' or 'đã bán' in HTML...")
        # Search using simple regex
        matches = re.finditer(r'([^<]{0,50}(sold|đã bán)[^>]{0,50})', html, re.IGNORECASE)
        count = 0
        for m in matches:
            count += 1
            print(f"Match {count}: {m.group(0).strip()}")
            if count >= 30:
                break
                
        if count == 0:
            print("No matches found for 'sold' or 'đã bán' in the text.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
