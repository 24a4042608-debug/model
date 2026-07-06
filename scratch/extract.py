import os
from bs4 import BeautifulSoup

def main():
    html_path = r"c:\Users\Admin\model\scratch\temp_shopee.html"
    output_path = r"c:\Users\Admin\model\extracted_links.txt"
    
    if not os.path.exists(html_path):
        print(f"Error: HTML file not found at {html_path}")
        return
        
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()
        
    soup = BeautifulSoup(html_content, "html.parser")
    anchors = soup.find_all("a", class_=lambda c: c and "contents" in c)
    if not anchors:
        anchors = soup.find_all("a", href=True)
        
    links = []
    for a in anchors:
        href = a.get("href")
        if href and ("-i." in href or "/product/" in href):
            if href.startswith("/"):
                href = "https://shopee.vn" + href
            links.append(href)
            
    # Load existing links
    unique_links = []
    if os.path.exists(output_path):
        with open(output_path, "r", encoding="utf-8") as f_in:
            for line in f_in:
                line = line.strip()
                if line and line not in unique_links:
                    unique_links.append(line)
                    
    # Add new links
    added_count = 0
    for l in links:
        if l not in unique_links:
            unique_links.append(l)
            added_count += 1
            
    with open(output_path, "w", encoding="utf-8") as f_out:
        for link in unique_links:
            f_out.write(link + "\n")
            
    # Avoid print emojis to prevent Windows console UnicodeEncodeErrors
    print(f"Extraction successful: added {added_count} new links. Total links in file: {len(unique_links)}.")

if __name__ == "__main__":
    main()
