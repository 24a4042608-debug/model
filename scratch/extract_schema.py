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
        
        matches = re.findall(r'<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html, re.DOTALL)
        print(f"Found {len(matches)} JSON-LD blocks.")
        
        for idx, m in enumerate(matches, 1):
            try:
                data = json.loads(m.strip())
                print(f"\n--- Block {idx} ---")
                print(json.dumps(data, indent=2, ensure_ascii=False)[:1000])
            except Exception as json_err:
                print(f"Error parsing block {idx}: {json_err}")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
