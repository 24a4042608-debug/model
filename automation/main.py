import sys
import os
# Force UTF-8 console output for Windows terminal compatibility
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import time
import threading
from datetime import datetime
import uvicorn
from dotenv import load_dotenv

from .database.models import init_db, SessionLocal
from .database import repository
from .telegram_bot import send_telegram_message
from .seo.generator import run_seo_generator
from .facebook.content_generator import generate_fb_content
from .facebook.publisher import publish_to_facebook

load_dotenv()

# ==========================================
# BACKGROUND SCHEDULER SYSTEM
# ==========================================

def run_scheduler_daemon():
    print("[Scheduler] Bắt đầu hàng đợi tiến trình tự động (Scheduler Daemon)...")
    
    # We poll every 30 seconds to check matching time
    while True:
        try:
            now = datetime.now()
            current_time = now.strftime("%H:%M")
            
            # 1. 07:00 AM - Auto Publish FB Queue
            if current_time == "07:00":
                print(f"[Scheduler] {current_time} - Kích hoạt tự động Đăng Facebook Fanpage...")
                auto_publish_fb_posts()
                time.sleep(65) # Sleep to avoid double firing
                
            # 2. 23:00 PM - Auto Sync / Crawl TikTok list
            elif current_time == "23:00":
                print(f"[Scheduler] {current_time} - Kích hoạt tự động cào và đồng bộ sản phẩm mới...")
                auto_sync_tiktok_shop()
                time.sleep(65)
                
        except Exception as e:
            print(f"[Scheduler] Gặp lỗi trong Scheduler: {e}")
            
        time.sleep(30)

def auto_publish_fb_posts():
    db = SessionLocal()
    try:
        # Get pending facebook posts
        posts = repository.get_all_fb_posts(db)
        pending_posts = [p for p in posts if p.status == "Pending"]
        
        if not pending_posts:
            log_msg = "[Scheduler] Không tìm thấy bài viết nào đang chờ (Pending) trong hàng đợi."
            print(log_msg)
            send_telegram_message(log_msg)
            return

        # Publish up to 5 posts
        limit = 5
        published_count = 0
        
        for post in pending_posts[:limit]:
            product_id = post.product_id
            raw_prod = repository.get_raw_product_by_product_id(db, product_id)
            image_urls = raw_prod.images if raw_prod else []
            
            print(f"[Scheduler] Đang đăng bài cho sản phẩm ID {product_id}...")
            repository.update_fb_post_status(db, product_id, "Publishing")
            
            success, msg = publish_to_facebook(post.caption, image_urls)
            
            if success:
                repository.update_fb_post_status(db, product_id, "Posted")
                published_count += 1
                alert = f"🎉 [Scheduler] Tự động đăng thành công sản phẩm ID: {product_id}"
            else:
                repository.update_fb_post_status(db, product_id, "Failed")
                alert = f"❌ [Scheduler] Tự động đăng thất bại sản phẩm ID: {product_id}. Lỗi: {msg}"
                
            print(alert)
            send_telegram_message(alert)
                
        print(f"[Scheduler] Hoàn tất phiên đăng. Đã đăng thành công {published_count}/{len(pending_posts[:limit])} bài viết.")
    except Exception as e:
        print(f"[Scheduler] Lỗi trong auto_publish_fb_posts: {e}")
    finally:
        db.close()

def auto_sync_tiktok_shop():
    print("[Scheduler] Đồng bộ tự động đang bị khóa do module crawl dữ liệu đã được gỡ.")

# ==========================================
# SERVER MAIN ENTRY
# ==========================================

if __name__ == "__main__":
    print("====================================================")
    print("      E-COMMERCE AUTOMATION PLATFORM (STARTING)     ")
    print("====================================================")
    
    # 1. Initialize Database Tables
    print("[Core] Kiểm tra và khởi tạo các bảng cơ sở dữ liệu MySQL...")
    init_db()
    
    # 2. Start Telegram Bot Client (Managed dynamically in API startup lifespans now)
    print("[Core] Cổng kết nối Telegram Bot sẽ được quản lý bởi FastAPI Process...")
    
    # 3. Start Background Scheduler Thread
    print("[Core] Khởi động trình lập lịch công việc tự động (Scheduler)...")
    sched_thread = threading.Thread(target=run_scheduler_daemon, daemon=True)
    sched_thread.start()
    
    # 4. Start FastAPI REST API Server
    print("[Core] Khởi chạy FastAPI API server (cổng 8000)...")
    # We parse host/port from env or defaults
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8000))
    
    uvicorn.run("automation.api:app", host=host, port=port, reload=True)
