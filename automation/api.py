import os
import uuid
import shutil
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field

from .database.models import get_db, RawProduct, SeoProduct, FacebookPost
from .database import repository
from .crawler.shopee_crawler import crawl_shopee_shop_products, crawl_active_shopee_tab
from .seo.generator import run_seo_generator
from .facebook.content_generator import generate_fb_content
from .facebook.publisher import publish_to_facebook
from .telegram_bot import send_telegram_message


app = FastAPI(title="E-Commerce Automation API")

# Create uploads directory if not exists
os.makedirs("public/uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="public/uploads"), name="uploads")

# Add CORS Middleware to enable communication with Vite React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from decision_engine.api.router import router as decision_engine_router
app.include_router(decision_engine_router)

@app.on_event("startup")
def startup_event():
    print("[FastAPI Startup] Khởi chạy Telegram Bot...")
    try:
        from .telegram_bot import start_telegram_bot
        start_telegram_bot()
    except Exception as e:
        print(f"[FastAPI Startup] Lỗi khởi chạy Telegram Bot: {e}")

# ==========================================
# PYDANTIC SCHEMAS
# ==========================================

class RawProductCreate(BaseModel):
    product_id: str
    title: str
    description: Optional[str] = ""
    price: Optional[float] = 0.0
    price_text: Optional[str] = ""
    brand: Optional[str] = ""
    category: Optional[str] = ""
    details_json: Optional[str] = ""
    images: Optional[List[str]] = []
    video: Optional[str] = ""
    url: Optional[str] = ""
    rating_star: Optional[float] = None
    sold_count: Optional[int] = None

class RawProductUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    price_text: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    details_json: Optional[str] = None
    images: Optional[List[str]] = None
    video: Optional[str] = None
    url: Optional[str] = None

class CrawlRequest(BaseModel):
    url: str
    method: Optional[str] = "cdp"
    cookie: Optional[str] = None

class ShopCrawlRequest(BaseModel):
    url: str
    method: Optional[str] = "cdp"
    cookie: Optional[str] = None
    max_products: Optional[int] = 10

class SeoProductUpdate(BaseModel):
    seo_title: Optional[str] = None
    meta_description: Optional[str] = None
    slug: Optional[str] = None
    main_keyword: Optional[str] = None
    secondary_keywords: Optional[List[str]] = None
    usp: Optional[List[str]] = None
    target_customer: Optional[str] = None
    search_intent: Optional[str] = None
    seo_score: Optional[int] = None
    analysis: Optional[dict] = None

class FbPostUpdate(BaseModel):
    caption: Optional[str] = None
    hashtags: Optional[List[str]] = None
    status: Optional[str] = None
    retry: Optional[int] = None

class PublishRequest(BaseModel):
    fanpage_url: Optional[str] = None

class TelegramConfig(BaseModel):
    bot_token: str
    chat_id: str

@app.post("/api/launch-chrome")
def launch_chrome_debug():
    import subprocess
    import time
    try:
        chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")
        ]
        
        chrome_path = None
        for path in chrome_paths:
            if os.path.exists(path):
                chrome_path = path
                break
                
        if not chrome_path:
            raise HTTPException(status_code=404, detail="Không tìm thấy trình duyệt Google Chrome trên máy tính của bạn.")
            
        # Terminate any running Chrome instances to free up the profile for debugging
        subprocess.run("taskkill /f /im chrome.exe", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1)
        
        # Start Chrome on debugging port 9222 without custom profile (uses main default profile with active session)
        cmd = f'"{chrome_path}" --remote-debugging-port=9222'
        subprocess.Popen(cmd, shell=True)
        
        return {"status": "success", "message": "Đã khởi động lại Chrome chính ở chế độ Debug."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khởi chạy Chrome: {str(e)}")

# ==========================================
# CRAWLER ENDPOINTS
# ==========================================

@app.get("/api/raw-products")
def list_raw_products(db: Session = Depends(get_db)):
    products = repository.get_all_raw_products(db)
    return products

@app.post("/api/raw-products")
def create_raw_product(product: RawProductCreate, db: Session = Depends(get_db)):
    return repository.create_raw_product(db, product.dict())

@app.put("/api/raw-products/{id}")
def update_raw_product(id: int, product: RawProductUpdate, db: Session = Depends(get_db)):
    db_product = repository.update_raw_product(db, id, product.dict(exclude_unset=True))
    if not db_product:
        raise HTTPException(status_code=404, detail="Raw product not found")
    return db_product

@app.delete("/api/raw-products/{id}")
def delete_raw_product(id: int, db: Session = Depends(get_db)):
    success = repository.delete_raw_product(db, id)
    if not success:
        raise HTTPException(status_code=404, detail="Raw product not found")
    return {"message": "Product deleted successfully"}

@app.delete("/api/raw-products")
def clear_all_raw_products(db: Session = Depends(get_db)):
    success = repository.clear_all_products(db)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to clear database")
    return {"message": "All products cleared successfully"}

@app.post("/api/upload")
def upload_file(file: UploadFile = File(...)):
    upload_dir = os.path.join("public", "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate unique filename to avoid overwrites
    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(upload_dir, unique_filename)
    
    # Save the file locally
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Không thể lưu file: {str(e)}")
        
    # Return the public relative URL
    return {"url": f"/uploads/{unique_filename}"}

@app.post("/api/crawl")
def trigger_crawl(req: CrawlRequest, db: Session = Depends(get_db)):
    if req.method == "http":
        from .crawler.shopee_http_crawler import crawl_product_http
        detail = crawl_product_http(req.url, db, cookie=req.cookie)
        if not detail:
            raise HTTPException(status_code=400, detail="Không thể cào sản phẩm. Vui lòng kiểm tra lại link hoặc cookie.")
        return {"status": "success", "message": "Cào sản phẩm thành công bằng HTTP Request!"}
    else:
        raise HTTPException(status_code=501, detail="Phương thức CDP cho link đơn lẻ chưa được hỗ trợ. Vui lòng chọn HTTP Request.")

# Global crawl progress tracking
import threading
crawl_progress = {
    "is_running": False,
    "shop_url": "",
    "total_products": 0,
    "crawled": 0,
    "added": 0,
    "skipped": 0,
    "errors": 0,
    "current_product": "",
    "logs": [],
    "status": "idle",  # idle, extracting_links, crawling_details, done, error
    "should_stop": False
}
crawl_lock = threading.Lock()

def crawl_log_callback(msg: str):
    """Callback to capture crawl logs for the frontend."""
    with crawl_lock:
        crawl_progress["logs"].append(msg)
        # Keep only last 100 logs to prevent memory leak
        if len(crawl_progress["logs"]) > 100:
            crawl_progress["logs"] = crawl_progress["logs"][-100:]
        
        # Parse progress from log messages
        if "BẮT ĐẦU CRAWL CHI TIẾT" in msg:
            import re
            match = re.search(r'(\d+) SẢN PHẨM', msg)
            if match:
                crawl_progress["total_products"] = int(match.group(1))
            crawl_progress["status"] = "crawling_details"
        elif msg.strip().startswith("✅") and "'" in msg:
            crawl_progress["crawled"] += 1
            crawl_progress["added"] += 1
            # Extract product name
            name_match = msg.split("'")
            if len(name_match) >= 2:
                crawl_progress["current_product"] = name_match[1][:60]
        elif "⏭️" in msg:
            crawl_progress["crawled"] += 1
            crawl_progress["skipped"] += 1
        elif "⚠️ Không lấy được" in msg or "❌" in msg:
            crawl_progress["crawled"] += 1
            crawl_progress["errors"] += 1
        elif "Tổng cộng:" in msg:
            import re
            match = re.search(r'(\d+) sản phẩm unique', msg)
            if match:
                crawl_progress["total_products"] = int(match.group(1))
        elif "HOÀN THÀNH" in msg:
            crawl_progress["status"] = "done"
            crawl_progress["is_running"] = False
        elif "Bắt đầu crawl" in msg:
            crawl_progress["status"] = "extracting_links"

def send_crawl_telegram_report():
    """Build and send a structured Telegram notification summarizing the crawl result."""
    with crawl_lock:
        status = crawl_progress["status"]
        added = crawl_progress["added"]
        skipped = crawl_progress["skipped"]
        errors = crawl_progress["errors"]
        total = crawl_progress["total_products"]
        url_info = crawl_progress["shop_url"]
        
        if status == "done":
            emoji = "✅"
            status_text = "Thành công"
        elif status == "error":
            emoji = "❌"
            status_text = "Thất bại/Có lỗi"
        else:
            emoji = "🔔"
            status_text = status.upper()
            
        msg = f"{emoji} [Crawl Shopee] Tiến trình cào đã hoàn thành!\n"
        msg += f"📌 Nguồn: {url_info}\n"
        msg += f"📊 Trạng thái: {status_text}\n"
        msg += f"🛒 Tổng số sản phẩm quét: {total}\n"
        msg += f"➕ Thêm mới: {added}\n"
        msg += f"⏭️ Bỏ qua (Đã có): {skipped}\n"
        msg += f"⚠️ Lỗi: {errors}"
        
    send_telegram_message(msg)

def shop_crawl_worker(url: str, method: str = "cdp", cookie: str = None, max_products: int = 10):
    with crawl_lock:
        crawl_progress["is_running"] = True
        crawl_progress["should_stop"] = False
        crawl_progress["shop_url"] = url
        crawl_progress["total_products"] = 0
        crawl_progress["crawled"] = 0
        crawl_progress["added"] = 0
        crawl_progress["skipped"] = 0
        crawl_progress["errors"] = 0
        crawl_progress["current_product"] = ""
        crawl_progress["logs"] = []
        crawl_progress["status"] = "extracting_links"
    
    db = next(get_db())
    try:
        def check_stop():
            with crawl_lock:
                return crawl_progress.get("should_stop", False)
        if method == "http":
            from .crawler.shopee_http_crawler import crawl_shop_http
            crawl_shop_http(
                shop_url=url,
                db=db,
                cookie=cookie,
                max_products=max_products,
                log_callback=crawl_log_callback,
                check_stop_callback=check_stop
            )
        else:
            crawl_shopee_shop_products(
                url, db, 
                log_callback=crawl_log_callback, 
                max_products=max_products, 
                check_stop_callback=check_stop
            )
    except Exception as e:
        print(f"Error in background shop crawl: {e}")
        with crawl_lock:
            crawl_progress["status"] = "error"
            crawl_progress["logs"].append(f"❌ Lỗi nghiêm trọng: {e}")
    finally:
        with crawl_lock:
            crawl_progress["is_running"] = False
            if crawl_progress["status"] != "error":
                crawl_progress["status"] = "done"
        db.close()
        send_crawl_telegram_report()

@app.post("/api/crawl-shop")
def trigger_shop_crawl(req: ShopCrawlRequest, background_tasks: BackgroundTasks):
    if crawl_progress.get("is_running"):
        raise HTTPException(status_code=409, detail="Đang có một tiến trình crawl đang chạy. Vui lòng đợi hoàn thành.")
    background_tasks.add_task(shop_crawl_worker, req.url, req.method, req.cookie, req.max_products)
    return {"status": "Shop crawl triggered in background", "message": "Đang bắt đầu crawl cửa hàng..."}

def active_tab_crawl_worker():
    with crawl_lock:
        crawl_progress["is_running"] = True
        crawl_progress["should_stop"] = False
        crawl_progress["shop_url"] = "CDP Active Tab"
        crawl_progress["total_products"] = 0
        crawl_progress["crawled"] = 0
        crawl_progress["added"] = 0
        crawl_progress["skipped"] = 0
        crawl_progress["errors"] = 0
        crawl_progress["current_product"] = ""
        crawl_progress["logs"] = []
        crawl_progress["status"] = "extracting_links"
    
    db = next(get_db())
    try:
        def check_stop():
            with crawl_lock:
                return crawl_progress.get("should_stop", False)
        crawl_active_shopee_tab(db, log_callback=crawl_log_callback, check_stop_callback=check_stop)
    except Exception as e:
        print(f"Error in background active tab crawl: {e}")
        with crawl_lock:
            crawl_progress["status"] = "error"
            crawl_progress["logs"].append(f"❌ Lỗi nghiêm trọng: {e}")
    finally:
        with crawl_lock:
            crawl_progress["is_running"] = False
            if crawl_progress["status"] != "error":
                crawl_progress["status"] = "done"
        db.close()
        send_crawl_telegram_report()

@app.post("/api/crawl-active-tab")
def trigger_active_tab_crawl(background_tasks: BackgroundTasks):
    if crawl_progress.get("is_running"):
        raise HTTPException(status_code=409, detail="Đang có một tiến trình crawl đang chạy. Vui lòng đợi hoàn thành.")
    background_tasks.add_task(active_tab_crawl_worker)
    return {"status": "Active tab crawl triggered in background", "message": "Đang bắt đầu crawl từ tab trình duyệt hiện tại..."}

# ==========================================
# CHROME EXTENSION ENDPOINTS
# ==========================================

class ExtensionShopCrawlRequest(BaseModel):
    shop_url: str
    urls: List[str]

def extension_shop_crawl_worker(urls: List[str]):
    with crawl_lock:
        crawl_progress["is_running"] = True
        crawl_progress["should_stop"] = False
        crawl_progress["shop_url"] = "Chrome Extension Link List"
        crawl_progress["total_products"] = len(urls)
        crawl_progress["crawled"] = 0
        crawl_progress["added"] = 0
        crawl_progress["skipped"] = 0
        crawl_progress["errors"] = 0
        crawl_progress["current_product"] = ""
        crawl_progress["logs"] = [f"📥 Bắt đầu cào {len(urls)} links từ Chrome Extension..."]
        crawl_progress["status"] = "crawling_details"

    db = next(get_db())
    try:
        from .crawler.shopee_http_crawler import crawl_product_http
        for idx, url in enumerate(urls, 1):
            with crawl_lock:
                if crawl_progress.get("should_stop", False):
                    crawl_log_callback("🛑 Tiến trình cào đã được dừng bởi người dùng.")
                    break
            
            # Re-check duplication before request
            match = re.search(r'[iI]\.(\d+)\.(\d+)', url)
            if not match:
                match = re.search(r'/product/(\d+)/(\d+)', url)
            if match:
                product_id = f"{match.group(1)}_{match.group(2)}"
            else:
                import hashlib
                product_id = hashlib.md5(url.encode()).hexdigest()
                
            existing = repository.get_raw_product_by_product_id(db, product_id)
            if existing:
                crawl_log_callback(f"⏭️ Bỏ qua (Đã tồn tại trong DB): '{existing.title[:45]}...'")
                continue
                
            detail = crawl_product_http(url, db, log_callback=crawl_log_callback)
            
            time.sleep(5)
    except Exception as e:
        print(f"Error in extension shop background crawl: {e}")
        with crawl_lock:
            crawl_progress["status"] = "error"
            crawl_progress["logs"].append(f"❌ Lỗi: {e}")
    finally:
        with crawl_lock:
            crawl_progress["is_running"] = False
            if crawl_progress["status"] != "error":
                crawl_progress["status"] = "done"
        db.close()
        send_crawl_telegram_report()

@app.post("/api/extension/crawl")
def extension_crawl(product: RawProductCreate, db: Session = Depends(get_db)):
    # Save raw product
    db_raw = repository.create_raw_product(db, product.dict())
    
    # Download images locally
    local_images = []
    os.makedirs("public/images", exist_ok=True)
    for img_idx, img_url in enumerate(product.images[:10]):
        try:
            local_filename = f"{product.product_id}_{img_idx}.jpg"
            local_path = os.path.join("public", "images", local_filename)
            from .crawler.shopee_crawler import download_image
            if download_image(img_url, local_path):
                local_images.append(f"/images/{local_filename}")
        except Exception as img_err:
            print(f"Error downloading image from extension payload: {img_err}")
            
    # Update local paths
    if local_images:
        db_raw.images = local_images
        db.commit()
        db.refresh(db_raw)
        
    # Save to main products table
    username = product.brand or "shopee"
    main_product_data = {
        "keyword": username,
        "title": product.title,
        "price_text": product.price_text,
        "price_val": product.price,
        "rating_star": product.rating_star,
        "sold_count": product.sold_count,
        "image_url": product.images[0] if product.images else "",
        "local_image_path": local_images[0] if local_images else "",
        "seo_keywords": "",
        "seo_description": "",
        "product_url": product.url
    }
    repository.create_product(db, main_product_data)
    
    # Send Telegram notification
    try:
        msg = f"🔌 [Chrome Extension] Đã cào sản phẩm thành công!\n" \
              f"📌 Tiêu đề: {product.title[:80]}...\n" \
              f"💰 Giá: {product.price_text}\n" \
              f"🔗 Link: {product.url}"
        send_telegram_message(msg)
    except Exception as e:
        print(f"Error sending telegram notification for extension: {e}")
        
    return {"status": "success", "product_id": product.product_id}

@app.post("/api/extension/crawl-shop")
def extension_crawl_shop(req: ExtensionShopCrawlRequest, background_tasks: BackgroundTasks):
    if crawl_progress.get("is_running"):
        raise HTTPException(status_code=409, detail="Đang có một tiến trình crawl đang chạy. Vui lòng đợi hoàn thành.")
    background_tasks.add_task(extension_shop_crawl_worker, req.urls)
    return {"status": "Extension shop crawl triggered in background", "message": "Đang bắt đầu cào danh sách link từ extension..."}

@app.post("/api/crawl/stop")
def stop_crawl():
    with crawl_lock:
        if not crawl_progress["is_running"]:
            return {"message": "Không có tiến trình crawl nào đang hoạt động."}
        crawl_progress["should_stop"] = True
        crawl_progress["logs"].append("🛑 Nhận được yêu cầu dừng cào từ người dùng. Đang gửi tín hiệu dừng...")
    return {"message": "Đang dừng tiến trình crawl..."}

@app.get("/api/crawl-shop/status")
def get_crawl_status():
    """Get real-time crawl progress for frontend polling."""
    with crawl_lock:
        return {
            "is_running": crawl_progress["is_running"],
            "shop_url": crawl_progress["shop_url"],
            "status": crawl_progress["status"],
            "total_products": crawl_progress["total_products"],
            "crawled": crawl_progress["crawled"],
            "added": crawl_progress["added"],
            "skipped": crawl_progress["skipped"],
            "errors": crawl_progress["errors"],
            "current_product": crawl_progress["current_product"],
            "logs": crawl_progress["logs"][-20:]  # Last 20 logs
        }

# ==========================================
# SEO OPTIMIZER ENDPOINTS
# ==========================================

@app.get("/api/seo-products")
def list_seo_products(db: Session = Depends(get_db)):
    return repository.get_all_seo_products(db)

@app.post("/api/seo-products/{product_id}")
def trigger_seo_optimization(product_id: str, db: Session = Depends(get_db)):
    raw_prod = repository.get_raw_product_by_product_id(db, product_id)
    if not raw_prod:
        raise HTTPException(status_code=404, detail="Raw product not found")
    
    try:
        seo_data = run_seo_generator(raw_prod.title, raw_prod.description, raw_prod.brand)
        seo_prod = repository.create_or_update_seo_product(db, product_id, seo_data)
        return seo_prod
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SEO generation failed: {str(e)}")

@app.put("/api/seo-products/{product_id}")
def update_seo_product(product_id: str, seo_prod: SeoProductUpdate, db: Session = Depends(get_db)):
    db_seo = repository.create_or_update_seo_product(db, product_id, seo_prod.dict(exclude_unset=True))
    return db_seo

@app.delete("/api/seo-products/{product_id}")
def delete_seo_product(product_id: str, db: Session = Depends(get_db)):
    success = repository.delete_seo_product(db, product_id)
    if not success:
        raise HTTPException(status_code=404, detail="SEO product not found")
    return {"message": "SEO metadata deleted"}

# ==========================================
# FACEBOOK QUEUE ENDPOINTS
# ==========================================

@app.get("/api/fb-queue")
def list_fb_queue(db: Session = Depends(get_db)):
    return repository.get_all_fb_posts(db)

@app.post("/api/fb-queue/{product_id}")
def generate_fb_post_in_queue(product_id: str, db: Session = Depends(get_db)):
    raw_prod = repository.get_raw_product_by_product_id(db, product_id)
    seo_prod = repository.get_seo_product_by_product_id(db, product_id)
    
    if not raw_prod or not seo_prod:
        raise HTTPException(status_code=400, detail="Ensure raw product and SEO optimization exist first")
        
    try:
        fb_data = generate_fb_content(
            raw_prod.title, seo_prod.seo_title, seo_prod.meta_description,
            seo_prod.main_keyword, seo_prod.secondary_keywords, seo_prod.usp
        )
        fb_post = repository.create_or_update_fb_post(db, product_id, fb_data)
        return fb_post
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"FB post generation failed: {str(e)}")

@app.put("/api/fb-queue/{product_id}")
def update_fb_queue_post(product_id: str, fb_update: FbPostUpdate, db: Session = Depends(get_db)):
    db_post = repository.create_or_update_fb_post(db, product_id, fb_update.dict(exclude_unset=True))
    return db_post

@app.delete("/api/fb-queue/{product_id}")
def delete_fb_post_from_queue(product_id: str, db: Session = Depends(get_db)):
    success = repository.delete_fb_post(db, product_id)
    if not success:
        raise HTTPException(status_code=404, detail="Facebook post not found in queue")
    return {"message": "Facebook post removed from queue"}

# Worker function for background publish
def publish_worker(product_id: str, caption: str, images: list, fanpage_url: str = None):
    db = next(get_db())
    try:
        repository.update_fb_post_status(db, product_id, "Publishing")
        success, msg = publish_to_facebook(caption, images, fanpage_url)
        if success:
            repository.update_fb_post_status(db, product_id, "Posted")
        else:
            repository.update_fb_post_status(db, product_id, "Failed")
    except Exception as e:
        print(f"Error in bg publish: {e}")
        repository.update_fb_post_status(db, product_id, "Failed")
    finally:
        db.close()

@app.post("/api/fb-publish/{product_id}")
def trigger_publish_to_facebook(product_id: str, background_tasks: BackgroundTasks, req: Optional[PublishRequest] = None, db: Session = Depends(get_db)):
    fb_post = repository.get_fb_post_by_product_id(db, product_id)
    if not fb_post:
        raise HTTPException(status_code=404, detail="Facebook post not found in queue")
        
    raw_prod = repository.get_raw_product_by_product_id(db, product_id)
    image_urls = raw_prod.images if raw_prod else []
    
    fanpage_url = req.fanpage_url if req else None
    
    # Run publishing asynchronously in background tasks
    background_tasks.add_task(publish_worker, product_id, fb_post.caption, image_urls, fanpage_url)
    
    # Mark state as Publishing immediately
    repository.update_fb_post_status(db, product_id, "Publishing")
    return {"status": "Publishing task triggered in background"}

@app.get("/api/system-status")
def get_system_status(db: Session = Depends(get_db)):
    # Stats
    raw_count = len(repository.get_all_raw_products(db))
    seo_count = len(repository.get_all_seo_products(db))
    fb_posts = repository.get_all_fb_posts(db)
    
    pending = len([p for p in fb_posts if p.status == "Pending"])
    posted = len([p for p in fb_posts if p.status == "Posted"])
    failed = len([p for p in fb_posts if p.status == "Failed"])
    
    return {
        "raw_products_count": raw_count,
        "seo_products_count": seo_count,
        "facebook_queue": {
            "pending": pending,
            "posted": posted,
            "failed": failed,
            "total": len(fb_posts)
        },
        "telegram_status": "Active" if os.getenv("TELEGRAM_BOT_TOKEN") else "Disabled",
        "gemini_status": "Configured" if os.getenv("GEMINI_API_KEY") else "Simulation Mode"
    }

@app.get("/api/telegram-config")
def get_telegram_config():
    return {
        "bot_token": os.getenv("TELEGRAM_BOT_TOKEN", ""),
        "chat_id": os.getenv("TELEGRAM_CHAT_ID", "")
    }

@app.post("/api/telegram-config")
def save_telegram_config(config: TelegramConfig):
    try:
        env_path = ".env"
        lines = []
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                
        token_found = False
        chat_id_found = False
        
        new_lines = []
        for line in lines:
            if line.strip().startswith("TELEGRAM_BOT_TOKEN="):
                new_lines.append(f"TELEGRAM_BOT_TOKEN={config.bot_token}\n")
                token_found = True
            elif line.strip().startswith("TELEGRAM_CHAT_ID="):
                new_lines.append(f"TELEGRAM_CHAT_ID={config.chat_id}\n")
                chat_id_found = True
            else:
                new_lines.append(line)
                
        if not token_found:
            new_lines.append(f"TELEGRAM_BOT_TOKEN={config.bot_token}\n")
        if not chat_id_found:
            new_lines.append(f"TELEGRAM_CHAT_ID={config.chat_id}\n")
            
        with open(env_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
            
        # Update running process variables
        os.environ["TELEGRAM_BOT_TOKEN"] = config.bot_token
        os.environ["TELEGRAM_CHAT_ID"] = config.chat_id
        
        # Start/Restart the bot thread with the new config!
        try:
            from .telegram_bot import start_telegram_bot
            start_telegram_bot()
        except Exception as bot_err:
            print(f"Error restarting Telegram bot: {bot_err}")
            
        return {"status": "success", "message": "Đã lưu cấu hình Telegram thành công!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Không thể lưu cấu hình Telegram: {str(e)}")

