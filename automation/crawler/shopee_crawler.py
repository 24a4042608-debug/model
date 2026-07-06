"""
Shopee Shop Crawler - Crawl products from a Shopee shop page.
Uses Chrome DevTools Protocol (CDP) to connect to the user's running Chrome browser
(which has proper cookies/sessions), and uses BeautifulSoup to parse data.
"""

import os
import sys
import re
import json
import time
import requests
from datetime import datetime
from sqlalchemy.orm import Session

# Force UTF-8 console output for Windows terminal compatibility
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from automation.database.models import RawProduct, Product
from automation.database import repository

# Configure remote debugging port
CDP_PORT = 9222

def parse_username_from_shopee_url(url: str) -> str:
    """Extract username from shopee shop URL."""
    cleaned = url.split('#')[0].split('?')[0]
    if cleaned.endswith('/'):
        cleaned = cleaned[:-1]
    return cleaned.split('/')[-1]

def download_image(url: str, filepath: str) -> bool:
    """Download image to local folder."""
    try:
        if url.startswith("//"):
            url = "https:" + url
        elif not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url
            
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
        }
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            with open(filepath, 'wb') as f:
                f.write(r.content)
            return True
    except Exception as e:
        print(f"Error downloading image: {e}")
    return False

def extract_product_links_with_soup(html_content: str) -> list:
    """Parse Shopee shop page to extract product links using BeautifulSoup."""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Shopee product items use class 'contents' on their main anchor
    anchors = soup.find_all('a', class_=lambda c: c and 'contents' in c)
    if not anchors:
        anchors = soup.find_all('a', href=True)
        
    links = []
    for a in anchors:
        href = a.get('href')
        if href and ('-i.' in href or '/product/' in href):
            # Convert relative href to absolute
            if href.startswith('/'):
                href = "https://shopee.vn" + href
            links.append(href)
            
    # De-duplicate preserving order
    unique_links = []
    for link in links:
        if link not in unique_links:
            unique_links.append(link)
    return unique_links

def extract_sold_counts_from_shop(html_content: str) -> dict:
    """Extract mapping of product_id -> sold_count integer from shop page HTML."""
    from bs4 import BeautifulSoup
    import re
    
    soup = BeautifulSoup(html_content, 'html.parser')
    anchors = soup.find_all('a', href=True)
    
    mapping = {}
    for a in anchors:
        href = a.get('href', '')
        # Extract product_id from href
        match = re.search(r'[iI]\.(\d+)\.(\d+)', href)
        if not match:
            match = re.search(r'/product/(\d+)/(\d+)', href)
        if not match:
            continue
            
        product_id = f"{match.group(1)}_{match.group(2)}"
        
        # Look for sold count in text elements inside this anchor
        sold_text = None
        for text in a.find_all(string=True):
            t = text.strip()
            if 'sold' in t.lower() or 'đã bán' in t.lower():
                sold_text = t
                break
                
        if sold_text:
            # Parse sold count (e.g. "1000k+ sold" -> 1000000, "56 sold" -> 56)
            try:
                # Remove non-digits but keep k/K
                cleaned = sold_text.lower().replace('sold', '').replace('đã bán', '').strip()
                match_val = re.search(r'([\d\.,]+)\s*([kK]?)', cleaned)
                if match_val:
                    val = float(match_val.group(1).replace(',', '.'))
                    if match_val.group(2).lower() == 'k':
                        val *= 1000
                    mapping[product_id] = int(round(val))
            except Exception as e:
                print(f"Error parsing sold count '{sold_text}': {e}")
                
    return mapping

def extract_product_detail_with_soup(html_content: str, sold_count_fallback: int = None) -> dict:
    """Parse Shopee product page HTML content to extract details using BeautifulSoup."""
    from bs4 import BeautifulSoup
    import re
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    result = {
        "title": "",
        "price_text": "",
        "price": 0.0,
        "category": "",
        "details": {},
        "description": "",
        "images": [],
        "video": "",
        "rating_star": None,
        "sold_count": None
    }
    
    # 1. TITLE
    try:
        wbvl_div = soup.find('div', class_=lambda c: c and 'WBVL_7' in c)
        if wbvl_div:
            h1 = wbvl_div.find('h1')
            if h1:
                result["title"] = h1.get_text(strip=True)
        
        if not result["title"]:
            h1 = soup.find('h1', class_=lambda c: c and 'vR6K3w' in c)
            if h1:
                result["title"] = h1.get_text(strip=True)
                
        if not result["title"]:
            h1 = soup.find('h1')
            if h1:
                result["title"] = h1.get_text(strip=True)
    except Exception as e:
        print(f"Error parsing title: {e}")
        
    # 2. PRICE
    try:
        # Check standard Shopee price selectors
        price_selectors = [('div', 'pmmxKx'), ('div', 'G27FPf')]
        for tag, cls in price_selectors:
            el = soup.find(tag, class_=lambda c: c and cls in c)
            if el:
                text = el.get_text(strip=True)
                if text and ('₫' in text or any(char.isdigit() for char in text)):
                    result["price_text"] = text
                    break
                    
        if not result["price_text"]:
            el = soup.find('span', class_=lambda c: c and 'price' in c.lower())
            if el:
                result["price_text"] = el.get_text(strip=True)
                
        if not result["price_text"]:
            # Fallback: scan all divs for price starting with ₫
            for div in soup.find_all('div'):
                text = div.get_text(strip=True)
                if text.startswith('₫') and len(text) < 30:
                    result["price_text"] = text
                    break
                    
        if result["price_text"]:
            nums = "".join(filter(str.isdigit, result["price_text"]))
            if nums:
                result["price"] = float(nums)
    except Exception as e:
        print(f"Error parsing price: {e}")
        
    # 3. DETAILS & CATEGORY
    try:
        # Find product details section
        detail_section = soup.find('div', class_=lambda c: c and 'product-detail' in c)
        if not detail_section:
            detail_section = soup
            
        rows = detail_section.find_all('div', class_=lambda c: c and 'ybxj32' in c)
        for row in rows:
            key_el = row.find('h3') or row.find('label')
            if key_el:
                key = key_el.get_text(strip=True)
                # Value is the remaining text inside row (excluding the key element)
                val_text = ""
                # Handle Category breadcrumbs specifically
                if 'Danh Mục' in key or 'Category' in key:
                    breadcrumbs = row.find_all('a', class_=lambda c: c and 'EtYbJs' in c)
                    parts = []
                    for a in breadcrumbs:
                        t = a.get_text(strip=True)
                        if t and t != 'Shopee':
                            parts.append(t)
                    val_text = " > ".join(parts)
                    result["category"] = val_text
                else:
                    # Generic row value
                    for child in row.children:
                        if child != key_el:
                            t = child.get_text(strip=True)
                            if t:
                                val_text = t
                                break
                if key and val_text:
                    result["details"][key] = val_text
    except Exception as e:
        print(f"Error parsing details: {e}")
        
    # 4. DESCRIPTION
    try:
        sections = soup.find_all('section', class_=lambda c: c and 'I_DV_3' in c)
        for section in sections:
            heading = section.find('h2')
            if heading and 'MÔ TẢ' in heading.get_text().upper():
                desc_div = section.find('div', class_=lambda c: c and ('Gf4Ro0' in c or 'e8lZp3' in c))
                if desc_div:
                    result["description"] = desc_div.get_text(strip=True)
                    break
    except Exception as e:
        print(f"Error parsing description: {e}")
        
    # 5. IMAGES
    try:
        image_set = set()
        
        # Check thumbnails in airUhU
        thumb_divs = soup.find_all('div', class_=lambda c: c and 'airUhU' in c)
        for div in thumb_divs:
            for img in div.find_all('img'):
                src = img.get('src') or ''
                srcset = img.get('srcset') or ''
                if srcset:
                    for s in srcset.split(','):
                        url = s.strip().split(' ')[0]
                        if url and 'susercontent.com' in url:
                            # Clean resize suffix to get high res image
                            clean_url = re.sub(r'@resize_w\d+_nl', '', url).split('_tn')[0]
                            image_set.add(clean_url)
                elif src and 'susercontent.com' in src:
                    clean_url = re.sub(r'@resize_w\d+_nl', '', src).split('_tn')[0]
                    image_set.add(clean_url)
                    
        # Check main images in xxW0BG or UdI7e2
        main_divs = soup.find_all('div', class_=lambda c: c and ('xxW0BG' in c or 'UdI7e2' in c))
        for div in main_divs:
            for img in div.find_all('img'):
                src = img.get('src') or ''
                srcset = img.get('srcset') or ''
                if srcset:
                    for s in srcset.split(','):
                        url = s.strip().split(' ')[0]
                        if url and 'susercontent.com' in url:
                            clean_url = re.sub(r'@resize_w\d+_nl', '', url).split('_tn')[0]
                            image_set.add(clean_url)
                elif src and 'susercontent.com' in src:
                    clean_url = re.sub(r'@resize_w\d+_nl', '', src).split('_tn')[0]
                    image_set.add(clean_url)
                    
        # Fallback to any susercontent image
        if not image_set:
            for img in soup.find_all('img', src=True):
                src = img.get('src')
                if src and 'susercontent.com' in src:
                    clean_url = re.sub(r'@resize_w\d+_nl', '', src).split('_tn')[0]
                    image_set.add(clean_url)
                    
        cleaned_images = []
        for img_url in image_set:
            if img_url.startswith("//"):
                img_url = "https:" + img_url
            elif not img_url.startswith("http://") and not img_url.startswith("https://"):
                img_url = "https://" + img_url
            cleaned_images.append(img_url)
            
        result["images"] = cleaned_images[:10]
    except Exception as e:
        print(f"Error parsing images: {e}")
        
    # 6. VIDEO
    try:
        video_el = soup.find('video', src=True)
        if video_el and 'susercontent' in video_el.get('src'):
            result["video"] = video_el.get('src')
    except Exception as e:
        print(f"Error parsing video: {e}")
        
    # 7. RATING STAR & SOLD COUNT
    try:
        rating_el = soup.find(class_=lambda c: c and ('rating-star' in c or 'RatingStar' in c or 'F9uo3e' in c))
        if rating_el:
            try:
                val = float(rating_el.get_text(strip=True))
                if 1 <= val <= 5:
                    result["rating_star"] = val
            except:
                pass
                
        # Parse sold count
        for el in soup.find_all(['div', 'span']):
            text = el.get_text(strip=True).lower()
            if 'đã bán' in text or 'sold' in text:
                match = re.search(r'([\d\.,]+)\s*([kK]?)', text)
                if match:
                    try:
                        val = float(match.group(1).replace(',', '.'))
                        if match.group(2).lower() == 'k':
                            val *= 1000
                        result["sold_count"] = int(round(val))
                        break
                    except:
                        pass
    except Exception as e:
        print(f"Error parsing rating/sold count: {e}")
        
    # Try parsing JSON-LD schema as fallback
    try:
        import json
        matches = re.findall(r'<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html_content, re.DOTALL)
        for m in matches:
            try:
                data = json.loads(m.strip())
                product_schema = None
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and item.get("@type") == "Product":
                            product_schema = item
                            break
                elif isinstance(data, dict):
                    if data.get("@type") == "Product":
                        product_schema = data
                    elif "@graph" in data:
                        for item in data["@graph"]:
                            if item.get("@type") == "Product":
                                product_schema = item
                                break
                                
                if product_schema:
                    if (not result["title"] or len(result["title"]) < 2) and product_schema.get("name"):
                        result["title"] = product_schema.get("name").strip()
                    if (not result["description"] or len(result["description"]) < 2) and product_schema.get("description"):
                        result["description"] = product_schema.get("description").strip()
                    
                    # Rating star
                    agg_rating = product_schema.get("aggregateRating")
                    if isinstance(agg_rating, dict):
                        val = agg_rating.get("ratingValue")
                        if val and result["rating_star"] is None:
                            try:
                                result["rating_star"] = float(val)
                            except:
                                pass
                            
                    # Price
                    offers = product_schema.get("offers")
                    if isinstance(offers, dict):
                        price_val = offers.get("lowPrice") or offers.get("price")
                        if price_val and (result["price"] == 0.0 or not result["price_text"]):
                            try:
                                result["price"] = float(price_val)
                                val_int = int(float(price_val))
                                result["price_text"] = f"{val_int:,}₫".replace(",", ".")
                            except:
                                pass
            except:
                pass
    except Exception as schema_err:
        print(f"JSON-LD extraction failed: {schema_err}")
        
    if result["sold_count"] is None and sold_count_fallback is not None:
        result["sold_count"] = sold_count_fallback
        
    return result

def login_to_shopee(page, phone_number, password, log) -> bool:
    log("🔑 [Shopee Login] Kiểm tra trạng thái đăng nhập...")
    try:
        cookies = page.context.cookies()
        is_logged_in = any(c.get('name') == 'SPC_EC' for c in cookies)
        if is_logged_in:
            log("  ✅ Đã đăng nhập Shopee sẵn (phát hiện cookie SPC_EC).")
            return True
            
        page.goto("https://shopee.vn/", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(3000)
        
        cookies = page.context.cookies()
        if any(c.get('name') == 'SPC_EC' for c in cookies):
            log("  ✅ Đã đăng nhập Shopee sẵn (phát hiện cookie SPC_EC sau khi load trang chủ).")
            return True
    except Exception as e:
        log(f"  ⚠️ Lỗi khi kiểm tra cookie: {e}")
        
    log("  🔐 Tiến hành tự động đăng nhập tài khoản...")
    try:
        page.goto("https://shopee.vn/buyer/login", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(3000)
        
        login_key = page.wait_for_selector("input[name='loginKey'], input[placeholder*='Số điện thoại'], input[type='text']", timeout=15000)
        if login_key:
            login_key.fill("")
            login_key.type(phone_number, delay=100)
            
        password_input = page.wait_for_selector("input[name='password'], input[type='password']", timeout=10000)
        if password_input:
            password_input.fill("")
            password_input.type(password, delay=100)
            
        page.wait_for_timeout(1000)
        
        login_submit = None
        for sel in [
            "button:has-text('Đăng nhập')",
            "button:has-text('ĐĂNG NHẬP')",
            "button:has-text('Log In')",
            "button:has-text('LOG IN')",
            "button.wyxo7X",
            "button[type='submit']",
            "form button"
        ]:
            try:
                btn = page.query_selector(sel)
                if btn:
                    login_submit = btn
                    break
            except:
                pass

        if login_submit:
            login_submit.click()
            log("  👉 Đã điền thông tin và nhấn nút Đăng nhập.")
        else:
            log("  ⚠️ Không tìm thấy nút Đăng nhập. Vui lòng tự nhấn nút Đăng nhập.")
            
        log("  ⏳ Đang kiểm tra xác thực hoặc mã OTP...")
        for attempt in range(120):
            page.wait_for_timeout(1000)
            curr_url = page.url
            
            if "buyer/login" not in curr_url and "shopee.vn" in curr_url:
                log("  ✅ Đăng nhập Shopee thành công!")
                return True
                
            if attempt % 5 == 0:
                log("  ⚠️ Vui lòng kéo thanh trượt xác minh hoặc nhập OTP trên trình duyệt nếu có yêu cầu...")
                
        if "buyer/login" not in page.url:
            log("  ✅ Đăng nhập thành công!")
            return True
        else:
            log("  ❌ Hết thời gian chờ đăng nhập (45 giây). Vui lòng kiểm tra lại trình duyệt.")
            return False
            
    except Exception as e:
        log(f"  ❌ Lỗi trong quá trình đăng nhập: {e}")
        return False

def crawl_shopee_shop_products(shop_url: str, db: Session, log_callback=None, max_products: int = 0, phone_number: str = "0325277814", password: str = "Son2110abc@", check_stop_callback=None) -> int:
    """Crawl products from a Shopee shop page via CDP connection and BeautifulSoup."""
    def log(msg: str):
        print(msg)
        if log_callback:
            log_callback(msg)

    username = parse_username_from_shopee_url(shop_url)
    log(f"🔍 [Shopee Crawler] Bắt đầu crawl shop: '{username}'")
    log(f"🔍 [Shopee Crawler] URL: {shop_url}")

    total_added = 0

    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            # ============================
            # STEP 1: Connect to browser (CDP first, fallback to separate Chrome)
            # ============================
            browser = None
            context = None
            use_persistent = False
            
            log(f"🌐 [Shopee Crawler] Kết nối Chrome qua CDP (port {CDP_PORT})...")
            try:
                browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{CDP_PORT}")
                contexts = browser.contexts
                if contexts:
                    context = contexts[0]
                    page = context.new_page()
                    log(f"  ✅ Đã kết nối CDP thành công (sử dụng session Chrome hiện tại)")
                else:
                    raise Exception("No browser contexts found")
            except Exception as e:
                log(f"  ⚠️ CDP không khả dụng: {e}")
                log(f"  🔄 Khởi động Chrome riêng...")
                
                crawler_profile = os.path.join(
                    os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), 
                    "ShopeeAutoCrawler", "profile"
                )
                os.makedirs(crawler_profile, exist_ok=True)
                use_persistent = True
                
                try:
                    context = p.chromium.launch_persistent_context(
                        crawler_profile,
                        headless=False,
                        channel="chrome",
                        args=[
                            "--disable-blink-features=AutomationControlled",
                            "--no-first-run",
                            "--disable-default-apps",
                        ],
                        viewport={"width": 1280, "height": 720},
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                        ignore_default_args=["--enable-automation"],
                    )
                    page = context.pages[0] if context.pages else context.new_page()
                    log(f"  ✅ Đã mở Chrome riêng (headed mode)")
                except Exception as e2:
                    log(f"❌ Không thể mở trình duyệt: {e2}")
                    return 0

            # ============================
            # STEP 1.5: Login to Shopee if credentials provided
            # ============================
            if phone_number and password:
                login_to_shopee(page, phone_number, password, log)

            # ============================
            # STEP 2: Navigate to shop page & extract product links
            # ============================
            log(f"📦 [Shopee Crawler] Đang tải trang shop: {shop_url}")
            page.goto(shop_url, wait_until="domcontentloaded", timeout=30000)

            # Wait for products to render
            has_products = False
            try:
                page.wait_for_selector("a.contents", timeout=10000)
                has_products = True
            except Exception:
                pass

            if not has_products:
                log("⚠️ Không tìm thấy sản phẩm nào trên trang shop. Có thể Shopee yêu cầu xác thực hoặc giải Captcha.")
                if use_persistent:
                    log("👉 VUI LÒNG KIỂM TRA CỬA SỔ CHROME VỪA MỞ:")
                    log("   1. Giải Captcha hoặc Đăng nhập tài khoản Shopee của bạn trên cửa sổ Chrome đó.")
                    log("   2. Crawler sẽ tự động tải lại trang sau 30 giây...")
                    page.wait_for_timeout(30000)
                    
                    log("🔄 Đang tải lại trang shop...")
                    try:
                        page.goto(shop_url, wait_until="domcontentloaded", timeout=30000)
                        page.wait_for_selector("a.contents", timeout=15000)
                        log("  ✅ Đã tải được sản phẩm sau khi xác thực!")
                    except Exception:
                        log("❌ Vẫn không tải được sản phẩm. Dừng crawl.")
                        return 0
                else:
                    log("👉 VUI LÒNG KIỂM TRA TRÌNH DUYỆT CHROME ĐANG MỞ:")
                    log("   1. Giải Captcha hoặc Đăng nhập tài khoản Shopee của bạn trên trình duyệt đó.")
                    log("   2. Crawler sẽ tự động tải lại trang sau 20 giây...")
                    page.wait_for_timeout(20000)
                    
                    log("🔄 Đang tải lại trang shop...")
                    try:
                        page.goto(shop_url, wait_until="domcontentloaded", timeout=30000)
                        page.wait_for_selector("a.contents", timeout=15000)
                        log("  ✅ Đã tải được sản phẩm!")
                    except Exception:
                        log("❌ Vẫn không tải được sản phẩm. Dừng crawl.")
                        return 0

            page.wait_for_timeout(3000)

            # Scroll down smoothly to trigger Shopee lazy loading of all products
            def scroll_to_load_all():
                for i in range(12):
                    try:
                        page.evaluate(f"window.scrollTo(0, {i * 800})")
                        page.wait_for_timeout(1000)
                    except Exception as e:
                        if "closed" in str(e).lower() or "target closed" in str(e).lower():
                            return False
                        raise e
                return True

            # Extract links with pagination
            all_product_hrefs = []
            seen_hrefs = set()
            shop_sold_counts = {}
            browser_closed = False

            for page_num in range(1, 50):
                try:
                    if not scroll_to_load_all():
                        browser_closed = True
                        break

                    html_snap = page.content()
                    links = extract_product_links_with_soup(html_snap)
                    try:
                        counts_map = extract_sold_counts_from_shop(html_snap)
                        shop_sold_counts.update(counts_map)
                    except Exception as counts_err:
                        print(f"Error extracting sold counts: {counts_err}")
                    new_count = 0

                    for href in links:
                        if href not in seen_hrefs:
                            seen_hrefs.add(href)
                            all_product_hrefs.append(href)
                            new_count += 1

                    log(f"  📜 Trang {page_num}: {len(links)} SP trên trang ({new_count} mới, tổng: {len(all_product_hrefs)})")

                    # Check for Next Page button
                    next_btn = page.query_selector("button.shopee-icon-button--right")
                    if not next_btn or not next_btn.is_enabled():
                        log("  ✅ Không còn trang tiếp theo.")
                        break

                    # Click Next Page
                    next_btn.click()
                    page.wait_for_timeout(3000)
                except Exception as e:
                    error_msg = str(e)
                    if "closed" in error_msg.lower() or "target closed" in error_msg.lower():
                        log("  ⚠️ Trình duyệt bị đóng trong khi phân trang. Dừng phân trang.")
                        browser_closed = True
                        break
                    raise e

            log(f"\n🔗 [Shopee Crawler] Tổng cộng: {len(all_product_hrefs)} sản phẩm unique")

            # Filter valid product links
            valid_hrefs = [h for h in all_product_hrefs if '-i.' in h]
            log(f"✨ [Shopee Crawler] Đã lọc: {len(valid_hrefs)} sản phẩm hợp lệ")

            if max_products > 0:
                valid_hrefs = valid_hrefs[:max_products]
                log(f"⚙️ Giới hạn crawl: {max_products} sản phẩm")

            # ============================
            # STEP 3: Crawl Product Details (Visit each page)
            # ============================
            log(f"\n{'='*60}")
            log(f"📋 BẮT ĐẦU CRAWL CHI TIẾT {len(valid_hrefs)} SẢN PHẨM")
            log(f"{'='*60}\n")

            detail_page = context.new_page()
            consecutive_blocks = 0
            total_errors = 0

            for idx, full_url in enumerate(valid_hrefs, 1):
                if browser_closed:
                    break

                # Extract product_id from URL
                match = re.search(r'[iI]\.(\d+)\.(\d+)', full_url)
                if not match:
                    match = re.search(r'/product/(\d+)/(\d+)', full_url)
                    
                if match:
                    shop_id, item_id = match.group(1), match.group(2)
                    product_id = f"{shop_id}_{item_id}"
                else:
                    import hashlib
                    product_id = hashlib.md5(full_url.encode()).hexdigest()

                # Check duplication
                existing = repository.get_raw_product_by_product_id(db, product_id)
                if existing:
                    log(f"[{idx}/{len(valid_hrefs)}] ━━━━━━━━━━━━━━━━━━━━")
                    log(f"  ⏭️ Bỏ qua (Đã tồn tại trong DB): '{existing.title[:45]}...'")
                    
                    # Also ensure it exists in products table
                    main_existing = repository.get_product_by_title_and_keyword(db, existing.title, username)
                    if not main_existing:
                        image_url = ""
                        if existing.images:
                            if isinstance(existing.images, list):
                                image_url = existing.images[0] if existing.images else ""
                            elif isinstance(existing.images, str):
                                try:
                                    parsed = json.loads(existing.images)
                                    if isinstance(parsed, list) and parsed:
                                        image_url = parsed[0]
                                except:
                                    pass
                                    
                        main_product_data = {
                            "keyword": username,
                            "title": existing.title,
                            "price_text": existing.price_text,
                            "price_val": existing.price,
                            "rating_star": None,
                            "sold_count": None,
                            "image_url": image_url,
                            "local_image_path": "",
                            "seo_keywords": "",
                            "seo_description": "",
                            "product_url": full_url
                        }
                        repository.create_product(db, main_product_data)
                    continue

                if check_stop_callback and check_stop_callback():
                    log("🛑 Tiến trình cào đã được dừng bởi người dùng.")
                    break

                log(f"[{idx}/{len(valid_hrefs)}] ━━━━━━━━━━━━━━━━━━━━")
                
                try:
                    log(f"  📄 Đang tải chi tiết sản phẩm...")
                    detail_page.goto(full_url, wait_until="domcontentloaded", timeout=30000)

                    # Wait for SPA to render
                    try:
                        detail_page.wait_for_selector("div.WBVL_7, h1, div.product-detail", timeout=10000)
                    except Exception:
                        pass

                    detail_page.wait_for_timeout(2000)
                    
                    # Scroll down to trigger lazy loading of reviews and ratings
                    detail_page.evaluate("window.scrollBy(0, 500)")
                    detail_page.wait_for_timeout(1500)
                    detail_page.evaluate("window.scrollBy(0, 500)")
                    detail_page.wait_for_timeout(1500)

                    # Check anti-bot block
                    actual_url = detail_page.url
                    if "verify/traffic" in actual_url or "/error" in actual_url:
                        consecutive_blocks += 1
                        log(f"  ⚠️ Shopee anti-bot detected! (lần {consecutive_blocks})")
                        
                        if consecutive_blocks >= 3:
                            log(f"  🛑 Bị block liên tục {consecutive_blocks} lần. Đợi 30s...")
                            log(f"     👉 Vui lòng giải Captcha trên cửa sổ Chrome của bạn!")
                            detail_page.wait_for_timeout(30000)
                            consecutive_blocks = 0
                        else:
                            log(f"  ⏳ Đợi 10s rồi thử lại...")
                            detail_page.wait_for_timeout(10000)
                        
                        detail_page.goto(full_url, wait_until="domcontentloaded", timeout=30000)
                        detail_page.wait_for_timeout(5000)
                        actual_url = detail_page.url
                        
                        if "verify/traffic" in actual_url or "/error" in actual_url:
                            log(f"  ❌ Vẫn bị block. Bỏ qua SP này.")
                            total_errors += 1
                            continue

                    consecutive_blocks = 0

                    # Extract details using BeautifulSoup
                    detail = extract_product_detail_with_soup(
                        detail_page.content(), 
                        sold_count_fallback=shop_sold_counts.get(product_id)
                    )

                    if not detail["title"]:
                        log(f"  ⏳ Tiêu đề trống, đợi thêm 5s và thử lại...")
                        detail_page.wait_for_timeout(5000)
                        detail = extract_product_detail_with_soup(
                            detail_page.content(),
                            sold_count_fallback=shop_sold_counts.get(product_id)
                        )

                    if not detail["title"]:
                        log(f"  ⚠️ Không lấy được tiêu đề. Bỏ qua.")
                        total_errors += 1
                        continue

                    log(f"  🔗 URL: {actual_url[:80]}")

                    # Download images
                    local_images = []
                    os.makedirs("public/images", exist_ok=True)
                    for img_idx, img_url in enumerate(detail["images"][:10]):
                        try:
                            local_filename = f"{product_id}_{img_idx}.jpg"
                            local_path = os.path.join("public", "images", local_filename)
                            
                            # Download
                            if download_image(img_url, local_path):
                                local_images.append(f"/images/{local_filename}")
                        except Exception as img_err:
                            log(f"    ⚠️ Lỗi tải ảnh {img_idx}: {img_err}")

                    # Save to DB
                    product_data = {
                        "product_id": product_id,
                        "title": detail["title"],
                        "description": detail["description"],
                        "price": detail["price"],
                        "price_text": detail["price_text"],
                        "brand": detail["details"].get("Thương hiệu", "BYJANE"),
                        "category": detail["category"] or "Shopee",
                        "details_json": json.dumps(detail["details"], ensure_ascii=False),
                        "images": local_images,
                        "video": detail["video"],
                        "url": full_url,
                        "rating_star": detail["rating_star"],
                        "sold_count": detail["sold_count"]
                    }
                    repository.create_raw_product(db, product_data)
                    
                    # Save to main 'products' table
                    main_product_data = {
                        "keyword": username,
                        "title": detail["title"],
                        "price_text": detail["price_text"],
                        "price_val": detail["price"],
                        "rating_star": detail["rating_star"],
                        "sold_count": detail["sold_count"],
                        "image_url": detail["images"][0] if detail["images"] else "",
                        "local_image_path": local_images[0] if local_images else "",
                        "seo_keywords": "",
                        "seo_description": "",
                        "product_url": full_url
                    }
                    repository.create_product(db, main_product_data)
                    
                    total_added += 1
                    log(f"  ✅ '{detail['title'][:50]}...'")
                    log(f"     Giá: {detail['price_text']} | Ảnh: {len(local_images)} | Danh mục: {detail['category'][:40]}")

                    time.sleep(5)  # Rate limit

                except Exception as e:
                    error_msg = str(e)
                    log(f"  ❌ Lỗi: {error_msg}")
                    total_errors += 1

                    if "has been closed" in error_msg or "Target closed" in error_msg:
                        log(f"  🔄 Browser bị đóng, đang kết nối lại...")
                        try:
                            browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{CDP_PORT}")
                            contexts = browser.contexts
                            if contexts:
                                context = contexts[0]
                                detail_page = context.new_page()
                                log(f"  ✅ Đã kết nối lại thành công!")
                            else:
                                log(f"  ❌ Không thể kết nối lại. Dừng crawl.")
                                break
                        except Exception as re_err:
                            log(f"  ❌ Kết nối lại thất bại: {re_err}")
                            break

                    time.sleep(3)

            # Close page tabs safely
            try: page.close()
            except: pass
            
            if use_persistent:
                try: context.close()
                except: pass

            log(f"\n{'='*60}")
            log(f"🎉 [Shopee Crawler] HOÀN THÀNH CRAWL SHOP {username}")
            log(f"{'='*60}")
            log(f"  ✅ Đã thêm mới:          {total_added}")
            log(f"  ⏭️ Bỏ qua (đã có DB):    {len(valid_hrefs) - total_added - total_errors}")
            log(f"  ❌ Lỗi:                  {total_errors}")
            log(f"  📊 Tổng sản phẩm quét:   {len(valid_hrefs)}")
            log(f"{'='*60}\n")

    except Exception as e:
        log(f"❌ Lỗi nghiêm trọng: {e}")

    return total_added

def crawl_active_shopee_tab(db: Session, log_callback=None, check_stop_callback=None) -> int:
    """Connect to Chrome via CDP, find the active Shopee tab, reload it and crawl."""
    def log(msg: str):
        print(msg)
        if log_callback:
            log_callback(msg)

    log("🌐 [Active Tab Crawler] Kết nối Chrome qua CDP...")
    from playwright.sync_api import sync_playwright
    import re
    import json
    
    total_added = 0
    try:
        with sync_playwright() as p:
            try:
                browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{CDP_PORT}")
                context = browser.contexts[0]
            except Exception as e:
                log(f"❌ Không thể kết nối debug port {CDP_PORT}: {e}")
                return 0

            # Find active Shopee page
            shopee_page = None
            for page in context.pages:
                if "shopee.vn" in page.url:
                    shopee_page = page
                    break

            if not shopee_page:
                log("❌ Không tìm thấy tab Shopee nào đang mở trên trình duyệt.")
                return 0

            url = shopee_page.url
            log(f"✅ Đã tìm thấy tab Shopee: {url}")
            
            # Reload page to activate/wake it up
            log("🔄 Đang kích hoạt và tải lại tab để đảm bảo nội dung được hiển thị...")
            shopee_page.bring_to_front()
            try:
                shopee_page.reload(wait_until="domcontentloaded", timeout=45000)
            except Exception as re_err:
                log(f"⚠️ Cảnh báo tải lại: {re_err}")
            shopee_page.wait_for_timeout(6000)
            
            # Check page type
            is_product = "-i." in url or "/product/" in url
            if is_product:
                log("📝 Phát hiện trang Chi tiết Sản phẩm. Bắt đầu crawl...")
                
                # Scroll down to trigger lazy loading of reviews and ratings
                shopee_page.evaluate("window.scrollBy(0, 500)")
                shopee_page.wait_for_timeout(1500)
                shopee_page.evaluate("window.scrollBy(0, 500)")
                shopee_page.wait_for_timeout(1500)
                
                # Parse
                html_content = shopee_page.content()
                detail = extract_product_detail_with_soup(html_content)
                if not detail["title"]:
                    shopee_page.wait_for_timeout(5000)
                    detail = extract_product_detail_with_soup(shopee_page.content())
                    
                if not detail["title"]:
                    log("❌ Không thể parse chi tiết sản phẩm (Tiêu đề trống).")
                    return 0
                    
                # Crawl product details and insert
                # (extract product_id)
                match = re.search(r'[iI]\.(\d+)\.(\d+)', url)
                if not match:
                    match = re.search(r'/product/(\d+)/(\d+)', url)
                if match:
                    shop_id, item_id = match.group(1), match.group(2)
                    product_id = f"{shop_id}_{item_id}"
                else:
                    import hashlib
                    product_id = hashlib.md5(url.encode()).hexdigest()
                    
                existing = repository.get_raw_product_by_product_id(db, product_id)
                if existing:
                    log(f"⏭️ Bỏ qua (Đã tồn tại trong DB): '{existing.title[:45]}...'")
                    return 0
                    
                local_images = []
                os.makedirs("public/images", exist_ok=True)
                for img_idx, img_url in enumerate(detail["images"][:10]):
                    try:
                        local_filename = f"{product_id}_{img_idx}.jpg"
                        local_path = os.path.join("public", "images", local_filename)
                        if download_image(img_url, local_path):
                            local_images.append(f"/images/{local_filename}")
                    except Exception as img_err:
                        log(f"    ⚠️ Lỗi tải ảnh: {img_err}")
                        
                product_data = {
                    "product_id": product_id,
                    "title": detail["title"],
                    "description": detail["description"],
                    "price": detail["price"],
                    "price_text": detail["price_text"],
                    "brand": detail["details"].get("Thương hiệu", "BYJANE"),
                    "category": detail["category"] or "Shopee",
                    "details_json": json.dumps(detail["details"], ensure_ascii=False),
                    "images": local_images,
                    "video": detail["video"],
                    "url": url,
                    "rating_star": detail["rating_star"],
                    "sold_count": detail["sold_count"]
                }
                repository.create_raw_product(db, product_data)
                
                main_product_data = {
                    "keyword": "shopee",
                    "title": detail["title"],
                    "price_text": detail["price_text"],
                    "price_val": detail["price"],
                    "rating_star": detail["rating_star"],
                    "sold_count": detail["sold_count"],
                    "image_url": detail["images"][0] if detail["images"] else "",
                    "local_image_path": local_images[0] if local_images else "",
                    "seo_keywords": "",
                    "seo_description": "",
                    "product_url": url
                }
                repository.create_product(db, main_product_data)
                
                log(f"✅ Đã lưu sản phẩm thành công: '{detail['title'][:45]}...'")
                total_added = 1
            else:
                log("🛒 Phát hiện trang Cửa hàng / Danh mục. Bắt đầu crawl danh sách sản phẩm...")
                username = parse_username_from_shopee_url(url)
                
                log("⏳ Đang cuộn trang để tải tất cả sản phẩm...")
                for i in range(12):
                    shopee_page.evaluate(f"window.scrollTo(0, {i * 800})")
                    shopee_page.wait_for_timeout(1000)
                shopee_page.evaluate("window.scrollTo(0, 0)")
                shopee_page.wait_for_timeout(500)
                
                html_snap = shopee_page.content()
                links = extract_product_links_with_soup(html_snap)
                shop_sold_counts = {}
                try:
                    shop_sold_counts = extract_sold_counts_from_shop(html_snap)
                except Exception as counts_err:
                    log(f"⚠️ Error parsing sold counts from shop page: {counts_err}")
                valid_links = [l for l in links if '-i.' in l]
                log(f"✨ Tìm thấy {len(valid_links)} sản phẩm hợp lệ.")
                
                if not valid_links:
                    log("⚠️ Không tìm thấy sản phẩm nào trên trang này.")
                    return 0
                    
                # Save links
                local_path = r"c:\Users\Admin\model\extracted_links.txt"
                with open(local_path, "w", encoding="utf-8") as f:
                    for l in valid_links:
                        f.write(l + "\n")
                
                # Start crawling details
                log(f"📋 BẮT ĐẦU CRAWL CHI TIẾT {len(valid_links)} SẢN PHẨM")
                detail_page = context.new_page()
                total_errors = 0
                
                for idx, full_url in enumerate(valid_links, 1):
                    if check_stop_callback and check_stop_callback():
                        log("🛑 Tiến trình cào đã được dừng bởi người dùng.")
                        break

                    # Check duplication first
                    match = re.search(r'[iI]\.(\d+)\.(\d+)', full_url)
                    if not match:
                        match = re.search(r'/product/(\d+)/(\d+)', full_url)
                    if match:
                        product_id = f"{match.group(1)}_{match.group(2)}"
                    else:
                        import hashlib
                        product_id = hashlib.md5(full_url.encode()).hexdigest()
                        
                    existing = repository.get_raw_product_by_product_id(db, product_id)
                    if existing:
                        log(f"[{idx}/{len(valid_links)}] ━━━━━━━━━━━━━━━━━━━━")
                        log(f"  ⏭️ Bỏ qua (Đã tồn tại trong DB): '{existing.title[:45]}...'")
                        continue
                        
                    log(f"[{idx}/{len(valid_links)}] ━━━━━━━━━━━━━━━━━━━━")
                    try:
                        log(f"  📄 Đang tải chi tiết sản phẩm...")
                        detail_page.goto(full_url, wait_until="domcontentloaded", timeout=30000)
                        detail_page.wait_for_timeout(3000)
                        
                        # Scroll down to trigger lazy loading of reviews and ratings
                        detail_page.evaluate("window.scrollBy(0, 500)")
                        detail_page.wait_for_timeout(1500)
                        detail_page.evaluate("window.scrollBy(0, 500)")
                        detail_page.wait_for_timeout(1500)
                        
                        # Check block
                        if "verify/traffic" in detail_page.url or "/error" in detail_page.url:
                            log("  ⚠️ Phát hiện captcha. Vui lòng giải captcha trên Chrome!")
                            detail_page.wait_for_timeout(10000)
                            detail_page.goto(full_url, wait_until="domcontentloaded", timeout=30000)
                            detail_page.wait_for_timeout(4000)
                            if "verify/traffic" in detail_page.url:
                                log("  ❌ Vẫn bị block. Bỏ qua.")
                                total_errors += 1
                                continue
                                
                        detail = extract_product_detail_with_soup(
                            detail_page.content(), 
                            sold_count_fallback=shop_sold_counts.get(product_id)
                        )
                        if not detail["title"]:
                            detail_page.wait_for_timeout(5000)
                            detail = extract_product_detail_with_soup(
                                detail_page.content(), 
                                sold_count_fallback=shop_sold_counts.get(product_id)
                            )
                            
                        if not detail["title"]:
                            log("  ⚠️ Không thể lấy tiêu đề. Bỏ qua.")
                            total_errors += 1
                            continue
                            
                        local_images = []
                        os.makedirs("public/images", exist_ok=True)
                        for img_idx, img_url in enumerate(detail["images"][:10]):
                            try:
                                local_filename = f"{product_id}_{img_idx}.jpg"
                                local_path = os.path.join("public", "images", local_filename)
                                if download_image(img_url, local_path):
                                    local_images.append(f"/images/{local_filename}")
                            except Exception as img_err:
                                log(f"    ⚠️ Lỗi tải ảnh: {img_err}")
                                
                        product_data = {
                            "product_id": product_id,
                            "title": detail["title"],
                            "description": detail["description"],
                            "price": detail["price"],
                            "price_text": detail["price_text"],
                            "brand": detail["details"].get("Thương hiệu", "BYJANE"),
                            "category": detail["category"] or "Shopee",
                            "details_json": json.dumps(detail["details"], ensure_ascii=False),
                            "images": local_images,
                            "video": detail["video"],
                            "url": full_url,
                            "rating_star": detail["rating_star"],
                            "sold_count": detail["sold_count"]
                        }
                        repository.create_raw_product(db, product_data)
                        
                        main_product_data = {
                            "keyword": username,
                            "title": detail["title"],
                            "price_text": detail["price_text"],
                            "price_val": detail["price"],
                            "rating_star": detail["rating_star"],
                            "sold_count": detail["sold_count"],
                            "image_url": detail["images"][0] if detail["images"] else "",
                            "local_image_path": local_images[0] if local_images else "",
                            "seo_keywords": "",
                            "seo_description": "",
                            "product_url": full_url
                        }
                        repository.create_product(db, main_product_data)
                        
                        total_added += 1
                        log(f"  ✅ '{detail['title'][:45]}...'")
                        time.sleep(5)
                    except Exception as e:
                        log(f"  ❌ Lỗi: {e}")
                        total_errors += 1
                        time.sleep(3)
                        
                try: detail_page.close()
                except: pass
                
                log(f"\n{'='*60}")
                log(f"🎉 [Shopee Crawler] HOÀN THÀNH CRAWL SHOP TỪ TAB HIỆN TẠI")
                log(f"{'='*60}")
                log(f"  ✅ Đã thêm mới:          {total_added}")
                log(f"  ⏭️ Bỏ qua:               {len(valid_links) - total_added - total_errors}")
                log(f"  ❌ Lỗi:                  {total_errors}")
                log(f"  📊 Tổng sản phẩm quét:   {len(valid_links)}")
                log(f"{'='*60}\n")
                
    except Exception as e:
        log(f"❌ Lỗi nghiêm trọng: {e}")
        
    return total_added

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m automation.crawler.shopee_crawler <shop_url> [--max <max_products>]")
        sys.exit(1)
        
    shop_url = sys.argv[1]
    max_products = 0
    if "--max" in sys.argv:
        idx = sys.argv.index("--max")
        if idx + 1 < len(sys.argv):
            max_products = int(sys.argv[idx + 1])

    phone = "0325277814"
    password = "Son2110abc@"
    if "--phone" in sys.argv:
        idx = sys.argv.index("--phone")
        if idx + 1 < len(sys.argv):
            phone = sys.argv[idx + 1]
    if "--password" in sys.argv:
        idx = sys.argv.index("--password")
        if idx + 1 < len(sys.argv):
            password = sys.argv[idx + 1]

    from automation.database.models import init_db, SessionLocal
    init_db()
    db = SessionLocal()

    try:
        total = crawl_shopee_shop_products(
            shop_url=shop_url,
            db=db,
            max_products=max_products,
            phone_number=phone,
            password=password
        )
        print(f"\n🏁 Kết quả: Đã cào được {total} sản phẩm mới.")
    finally:
        db.close()
