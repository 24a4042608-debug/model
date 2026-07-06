import sys
import re
import json

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

def main():
    try:
        with open("scratch/product_page.html", "r", encoding="utf-8") as f:
            html = f.read()
            
        print("Searching for product data inside <script> blocks...")
        scripts = re.findall(r'<script\b[^>]*>(.*?)</script>', html, re.DOTALL)
        print(f"Found {len(scripts)} script blocks.")
        
        # Search for occurrences of numbers like 500000 or similar (since the product has 500k sold, let's search for 500000 or 500k)
        for idx, s in enumerate(scripts, 1):
            if len(s) > 1000:
                print(f"Script {idx} length: {len(s)}")
                # Search for keyword "historical_sold" or "sold" inside script
                for word in ["historical_sold", "sold_count", "soldCount", "amount_sold"]:
                    matches = list(re.finditer(word, s))
                    if matches:
                        print(f"  Found '{word}' {len(matches)} times in Script {idx}!")
                        # Print a snippet around the first match
                        pos = matches[0].start()
                        print(f"  Snippet: {s[max(0, pos-100):min(len(s), pos+150)]}")
                        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
