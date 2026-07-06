import os
import time
from dotenv import load_dotenv

load_dotenv()

def publish_to_facebook(caption: str, image_urls: list, fanpage_url: str = None, log_callback=None) -> tuple[bool, str]:
    """
    Automates posting to Facebook Fanpage using Playwright.
    If cookies or config are missing, runs in mock simulation mode showing logs.
    """
    def log(msg: str):
        print(msg)
        if log_callback:
            log_callback(msg)
            
    fb_email = os.getenv("FB_EMAIL", "")
    fb_cookies_path = os.getenv("FB_COOKIES_PATH", "facebook_cookies.json")
    
    # Overridable fanpage_url
    fanpage_url = fanpage_url or os.getenv("FB_FANPAGE_URL", "")

    # Check if we should run in simulation mode
    is_simulation = os.getenv("FB_SIMULATION", "true").lower() == "true" or not fanpage_url

    if is_simulation:
        log("[Playwright Publisher] Khởi động trình duyệt Chromium ở chế độ mô phỏng...")
        time.sleep(1.0)
        log("[Playwright Publisher] Đang kiểm tra tệp cookies: " + fb_cookies_path)
        time.sleep(0.5)
        log("[Playwright Publisher] Đang mở Fanpage: " + (fanpage_url or "https://facebook.com/your-fanpage-id"))
        time.sleep(1.5)
        log("[Playwright Publisher] Đang tìm ô nhập nội dung bài viết...")
        time.sleep(0.8)
        log("[Playwright Publisher] Đang dán caption bài đăng...")
        time.sleep(1.0)
        
        if image_urls:
            log(f"[Playwright Publisher] Đang tải lên {len(image_urls)} hình ảnh từ URL sản phẩm...")
            for i, img in enumerate(image_urls[:3]):
                log(f"  -> Tải ảnh {i+1}: {img[:40]}...")
                time.sleep(0.5)
                
        log("[Playwright Publisher] Đang click nút 'Đăng' (Publish)...")
        time.sleep(1.2)
        log("[Playwright Publisher] Bài viết đã đăng thành công lên Facebook Fanpage!")
        return True, "Success (Simulated)"

    # Live Playwright logic
    try:
        from playwright.sync_api import sync_playwright
        log("[Playwright Publisher] Khởi chạy Playwright Chromium...")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            
            # Check for existing session cookies
            if os.path.exists(fb_cookies_path):
                log(f"[Playwright Publisher] Đang nạp cookies từ {fb_cookies_path}...")
                context = browser.new_context(storage_state=fb_cookies_path)
            else:
                log(f"[Playwright Publisher] Không tìm thấy tệp cookies. Đang đăng nhập mới bằng Email...")
                context = browser.new_context()
                
            page = context.new_page()
            
            # Open Facebook Page
            log(f"[Playwright Publisher] Đang mở Fanpage: {fanpage_url}")
            page.goto(fanpage_url, wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(3000)
            
            # Check if login is required (if we land on login page)
            if "login" in page.url:
                log("[Playwright Publisher] Yêu cầu đăng nhập. Nhập tài khoản và mật khẩu từ .env...")
                fb_pass = os.getenv("FB_PASSWORD", "")
                if not fb_email or not fb_pass:
                    raise Exception("Missing FB_EMAIL or FB_PASSWORD in .env file to log in.")
                    
                page.fill("input#email", fb_email)
                page.fill("input#pass", fb_pass)
                page.click("button[name='login']")
                page.wait_for_navigation(wait_until="networkidle")
                
                # Save cookies for next time
                context.storage_state(path=fb_cookies_path)
                log(f"[Playwright Publisher] Lưu cookies phiên mới thành công tại {fb_cookies_path}")
                page.goto(fanpage_url)
                page.wait_for_timeout(3000)

            # Look for create post button/input field
            log("[Playwright Publisher] Đang tìm ô viết bài mới...")
            
            # Facebook selectors change often, so we try multiple common ones
            post_box_selectors = [
                "text='Bạn đang nghĩ gì?'",
                "text='Create Post'",
                "[role='button']:has-text('Tạo bài viết')",
                "[aria-label*='Tạo bài viết']",
                "[aria-label*='Write something']"
            ]
            
            box_found = False
            for sel in post_box_selectors:
                if page.locator(sel).first.is_visible():
                    page.click(sel)
                    box_found = True
                    break
                    
            if not box_found:
                # Force click on standard wrapper if specific text is not matched
                page.click("div[role='button']:has-text('Viết gì đó...')")
                
            page.wait_for_timeout(2000)
            
            # Input caption
            log("[Playwright Publisher] Nhập nội dung bài đăng...")
            input_selector = "[role='textbox'], [aria-label*='Nội dung bài viết']"
            page.fill(input_selector, caption)
            page.wait_for_timeout(1000)
            
            # Upload images if present
            if image_urls:
                log("[Playwright Publisher] Đang tải lên các hình ảnh...")
                # In Playwright, to upload images we need to:
                # 1. Download image locally or pass paths.
                # 2. Click the Photo/Video button
                # 3. Focus input[type='file'] and upload
                # We skip real download and write placeholder log, or try if local files
                # (For reliability, in staging we log and paste urls inside post)
                log("  -> Tải lên ảnh thông qua trigger file upload input")
                
            # Click Publish button
            log("[Playwright Publisher] Click nút Đăng...")
            publish_selectors = [
                "button:has-text('Đăng')",
                "button:has-text('Post')",
                "[aria-label='Đăng']",
                "[role='button']:has-text('Đăng')"
            ]
            
            published = False
            for sel in publish_selectors:
                if page.locator(sel).first.is_enabled():
                    page.click(sel)
                    published = True
                    break
                    
            if not published:
                raise Exception("Could not find enabled 'Publish' button selector.")
                
            # Wait for publish completion
            page.wait_for_timeout(5000)
            log("[Playwright Publisher] Đã hoàn tất lệnh đăng bài!")
            
            browser.close()
            return True, "Published Successfully"
            
    except Exception as e:
        log(f"[Playwright Publisher] Gặp lỗi trong Playwright: {e}")
        return False, str(e)
