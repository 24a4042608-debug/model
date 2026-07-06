import os
import threading
import telebot
from telebot.types import BotCommand, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.orm import Session
from .database.models import SessionLocal, RawProduct
from .database import repository
from .seo.generator import run_seo_generator
from .facebook.content_generator import generate_fb_content
from .facebook.publisher import publish_to_facebook
from .crawler.shopee_crawler import crawl_shopee_shop_products, crawl_active_shopee_tab

# Global state tracking for interactive user prompts
user_states = {}

def get_main_menu():
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("📊 Trạng thái & Thống kê", callback_data="cb_status"))
    markup.row(InlineKeyboardButton("💵 Báo cáo Lợi nhuận ROAS", callback_data="cb_profit_menu"))
    markup.row(InlineKeyboardButton("🔍 Tìm kiếm & Sản phẩm", callback_data="cb_products_menu"))
    return markup

def get_profit_menu():
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("📈 Báo cáo Tổng quan ROAS", callback_data="cb_profit_summary"))
    markup.row(InlineKeyboardButton("📦 Lợi nhuận theo ID sản phẩm", callback_data="cb_profit_by_product"))
    markup.row(
        InlineKeyboardButton("📅 Hôm nay", callback_data="cb_profit_today"),
        InlineKeyboardButton("📅 Tuần này", callback_data="cb_profit_week")
    )
    markup.row(
        InlineKeyboardButton("📅 Tháng này", callback_data="cb_profit_month"),
        InlineKeyboardButton("📅 Năm này", callback_data="cb_profit_year")
    )
    markup.row(InlineKeyboardButton("🔙 Quay lại Menu chính", callback_data="cb_back_main"))
    return markup

def get_products_menu():
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🔍 Tìm sản phẩm theo tên", callback_data="cb_product_search"))
    markup.row(InlineKeyboardButton("📦 5 Sản phẩm mới cào", callback_data="cb_products_list"))
    markup.row(InlineKeyboardButton("🔥 Top 5 Bán chạy", callback_data="cb_products_best"))
    markup.row(InlineKeyboardButton("⭐️ Top 5 Đánh giá cao", callback_data="cb_products_rated"))
    markup.row(InlineKeyboardButton("🔙 Quay lại Menu chính", callback_data="cb_back_main"))
    return markup

def get_crawl_menu():
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🔗 Cào từ URL Shop", callback_data="cb_crawl_by_url"))
    markup.row(InlineKeyboardButton("💻 Cào từ Tab đang mở", callback_data="cb_crawl_tab_run"))
    markup.row(InlineKeyboardButton("🔙 Quay lại Menu chính", callback_data="cb_back_main"))
    return markup

def get_marketing_menu():
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🏷️ Tối ưu hóa SEO bằng AI", callback_data="cb_run_seo_prompt"))
    markup.row(InlineKeyboardButton("📱 Viết bài đăng Facebook", callback_data="cb_run_fb_prompt"))
    markup.row(InlineKeyboardButton("🚀 Đăng bài đầu tiên trong hàng đợi", callback_data="cb_run_publish"))
    markup.row(InlineKeyboardButton("🔙 Quay lại Menu chính", callback_data="cb_back_main"))
    return markup

def get_back_button(submenu="main"):
    markup = InlineKeyboardMarkup()
    if submenu == "main":
        markup.row(InlineKeyboardButton("🔙 Quay lại Menu chính", callback_data="cb_back_main"))
    else:
        markup.row(InlineKeyboardButton("🔙 Quay lại Menu", callback_data=f"cb_back_{submenu}"))
    return markup



# Thread-safe db session helper
def get_db_session():
    return SessionLocal()

active_bot = None

def start_telegram_bot():
    global active_bot
    from dotenv import load_dotenv
    load_dotenv(override=True)
    
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
    
    if not token:
        print("[Telegram Bot] TELEGRAM_BOT_TOKEN is not set. Telegram service is disabled.")
        if active_bot:
            try:
                print("[Telegram Bot] Stopping existing bot polling...")
                active_bot.stop_polling()
                active_bot = None
            except:
                pass
        return None
        
    try:
        if active_bot:
            try:
                print("[Telegram Bot] Stopping existing bot polling thread...")
                active_bot.stop_polling()
            except Exception as e:
                print(f"[Telegram Bot] Error stopping old bot: {e}")
                
        bot = telebot.TeleBot(token)
        active_bot = bot
        
        # Đăng ký danh sách câu lệnh hiển thị trong Menu của Telegram Bot
        try:
            bot.set_my_commands([
                BotCommand("status", "Xem trạng thái hệ thống & hàng đợi Facebook"),
                BotCommand("profit", "Xem báo cáo doanh thu & lợi nhuận chiến dịch ROAS"),
                BotCommand("search", "Tìm mã sản phẩm (Product ID) theo tên/từ khóa"),
                BotCommand("products", "Danh sách 10 sản phẩm mới cào gần đây"),
                BotCommand("top", "Bảng vàng sản phẩm bán chạy & đánh giá cao"),
                BotCommand("bestselling", "Top 10 sản phẩm bán chạy nhất"),
                BotCommand("toprate", "Top 10 sản phẩm đánh giá tốt nhất"),
                BotCommand("crawl", "Cào sản phẩm Shopee từ URL shop debug"),
                BotCommand("crawltab", "Cào nhanh sản phẩm từ Tab Shopee đang hoạt động"),
                BotCommand("seo", "Tối ưu hóa SEO bằng AI Gemini cho sản phẩm"),
                BotCommand("fb", "Tạo bài đăng Facebook Fanpage cho sản phẩm"),
                BotCommand("publish", "Đăng bài viết trạng thái Pending lên Facebook")
            ])
            print("[Telegram Bot] Đăng ký danh sách câu lệnh thành công.")
        except Exception as e:
            print(f"[Telegram Bot] Lỗi đăng ký câu lệnh: {e}")
            
        print(f"[Telegram Bot] Bot is starting long polling...")
        
        # Helper function for product search
        def perform_search(message, keyword: str):
            db = get_db_session()
            try:
                keyword_clean = keyword.strip()
                if not keyword_clean:
                    bot.reply_to(message, "❌ Từ khóa tìm kiếm không được để trống.")
                    return
                
                # Search database
                from sqlalchemy import or_
                results = db.query(RawProduct).filter(
                    or_(
                        RawProduct.title.like(f"%{keyword_clean}%"),
                        RawProduct.product_id.like(f"%{keyword_clean}%")
                    )
                ).limit(10).all()
                
                if not results:
                    bot.reply_to(message, f"🔍 Không tìm thấy sản phẩm nào khớp với từ khóa: <b>{keyword_clean}</b>", parse_mode="HTML")
                    return
                
                response_lines = [
                    f"🔍 <b>KẾT QUẢ TÌM KIẾM CHO:</b> <i>{keyword_clean}</i>",
                    f"Hiển thị tối đa 10 sản phẩm khớp nhất. Nhấp vào ID để sao chép:",
                    "━━━━━━━━━━━━━━━━━━━"
                ]
                
                for idx, prod in enumerate(results, 1):
                    seo_prod = repository.get_seo_product_by_product_id(db, prod.product_id)
                    fb_post = repository.get_fb_post_by_product_id(db, prod.product_id)
                    
                    status_badges = []
                    if seo_prod:
                        status_badges.append("🏷️ SEO")
                    if fb_post:
                        status_badges.append(f"📱 FB ({fb_post.status})")
                    
                    status_str = f" [{', '.join(status_badges)}]" if status_badges else ""
                    
                    # Output line
                    line = f"{idx}. <b>{prod.title[:60]}...</b>\n"
                    line += f"   └ ID: <code>{prod.product_id}</code>{status_str}\n"
                    response_lines.append(line)
                    
                response_lines.append("━━━━━━━━━━━━━━━━━━━")
                response_lines.append("💡 <b>Gợi ý câu lệnh tiếp theo:</b>")
                response_lines.append(f"• Tối ưu SEO: <code>/seo [ID]</code>")
                response_lines.append(f"• Viết bài Facebook: <code>/fb [ID]</code>")
                
                bot.reply_to(message, "\n".join(response_lines), parse_mode="HTML")
            except Exception as e:
                bot.reply_to(message, f"❌ Lỗi trong quá trình tìm kiếm: <code>{str(e)}</code>", parse_mode="HTML")
            finally:
                db.close()

        # Command start & help
        @bot.message_handler(commands=['start', 'help'])
        def send_welcome(message):
            user_states[message.chat.id] = None
            welcome_text = """
🤖 <b>BẢNG ĐIỀU KHIỂN E-COMMERCE AI</b> 👋

Chào mừng bạn đến với hệ thống quản lý và tối ưu hóa bán hàng tự động.
Vui lòng lựa chọn các chức năng dưới đây từ Menu để tiếp tục:
            """
            bot.send_message(message.chat.id, welcome_text, parse_mode="HTML", reply_markup=get_main_menu())

        # Callback query handler for interactive inline keyboard menus
        @bot.callback_query_handler(func=lambda call: True)
        def handle_callback(call):
            chat_id = call.message.chat.id
            message_id = call.message.message_id
            data = call.data
            
            # Reset user state upon menu interaction/navigation
            user_states[chat_id] = None
            
            # --- MENU NAVIGATION & BACK BUTTONS ---
            if data == "cb_back_main":
                welcome_text = "🤖 <b>BẢNG ĐIỀU KHIỂN E-COMMERCE AI</b> 👋\n\nVui lòng lựa chọn các chức năng dưới đây từ Menu để tiếp tục:"
                try:
                    bot.edit_message_text(welcome_text, chat_id, message_id, parse_mode="HTML", reply_markup=get_main_menu())
                except Exception:
                    bot.send_message(chat_id, welcome_text, parse_mode="HTML", reply_markup=get_main_menu())
                    
            elif data == "cb_profit_menu" or data == "cb_back_profit":
                text = "💵 <b>BÁO CÁO DOANH THU & LỢI NHUẬN ROAS</b>\n\nChọn chế độ xem báo cáo lợi nhuận từ các tùy chọn dưới đây:"
                try:
                    bot.edit_message_text(text, chat_id, message_id, parse_mode="HTML", reply_markup=get_profit_menu())
                except Exception:
                    bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=get_profit_menu())
                    
            elif data == "cb_products_menu" or data == "cb_back_products":
                text = "🔍 <b>TÌM KIẾM & DANH SÁCH SẢN PHẨM</b>\n\nChọn một tùy chọn bên dưới để xem hoặc tìm kiếm:"
                try:
                    bot.edit_message_text(text, chat_id, message_id, parse_mode="HTML", reply_markup=get_products_menu())
                except Exception:
                    bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=get_products_menu())
                    
            elif data == "cb_crawl_menu" or data == "cb_back_crawl":
                text = "🛒 <b>CÀO DỮ LIỆU SẢN PHẨM SHOPEE</b>\n\nChọn phương thức cào dữ liệu bên dưới:"
                try:
                    bot.edit_message_text(text, chat_id, message_id, parse_mode="HTML", reply_markup=get_crawl_menu())
                except Exception:
                    bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=get_crawl_menu())
                    
            elif data == "cb_back_marketing":
                text = "🚀 <b>CÔNG CỤ AI MARKETING & FACEBOOK</b>\n\nChọn tác vụ tối ưu hóa hoặc xuất bản bài đăng Fanpage:"
                try:
                    bot.edit_message_text(text, chat_id, message_id, parse_mode="HTML", reply_markup=get_marketing_menu())
                except Exception:
                    bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=get_marketing_menu())
            
            elif data == "cb_marketing_menu":
                text = "🚀 <b>CÔNG CỤ AI MARKETING & FACEBOOK</b>\n\nChọn tác vụ tối ưu hóa hoặc xuất bản bài đăng Fanpage:"
                try:
                    bot.edit_message_text(text, chat_id, message_id, parse_mode="HTML", reply_markup=get_marketing_menu())
                except Exception:
                    bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=get_marketing_menu())
                    
            # --- SUBMENU ACTIONS ---
            
            # 1. Status
            elif data == "cb_status":
                db = get_db_session()
                try:
                    raw_count = len(repository.get_all_raw_products(db))
                    seo_count = len(repository.get_all_seo_products(db))
                    fb_posts = repository.get_all_fb_posts(db)
                    
                    pending = len([p for p in fb_posts if p.status == "Pending"])
                    posted = len([p for p in fb_posts if p.status == "Posted"])
                    failed = len([p for p in fb_posts if p.status == "Failed"])
                    
                    status_text = f"""
📊 <b>BÁO CÁO TRẠNG THÁI HỆ THỐNG</b>
━━━━━━━━━━━━━━━━━━━
🛒 <b>Dữ liệu sản phẩm:</b>
• Tổng sản phẩm đã cào (Raw DB): <b>{raw_count}</b> sản phẩm
• Đã tối ưu hóa SEO bằng AI: <b>{seo_count}</b> sản phẩm
• Tỷ lệ phủ SEO: <b>{((seo_count / raw_count * 100) if raw_count > 0 else 0):.1f}%</b>

📈 <b>Hàng đợi bài đăng Facebook:</b>
• Đang chờ duyệt (Pending): ⏳ <b>{pending}</b> bài viết
• Đã đăng thành công (Posted): ✅ <b>{posted}</b> bài viết
• Đăng thất bại (Failed): ❌ <b>{failed}</b> bài viết
• Tổng số bài viết trong queue: 📋 <b>{len(fb_posts)}</b>
━━━━━━━━━━━━━━━━━━━
                    """
                    bot.edit_message_text(status_text, chat_id, message_id, parse_mode="HTML", reply_markup=get_back_button("main"))
                except Exception as e:
                    bot.edit_message_text(f"❌ Lỗi: {e}", chat_id, message_id, reply_markup=get_back_button("main"))
                finally:
                    db.close()
            
            # 2. Profit Actions
            elif data == "cb_profit_summary":
                db = get_db_session()
                try:
                    from sqlalchemy import func
                    from .database.models import TrainingDataset
                    res = db.query(
                        func.sum(TrainingDataset.profit),
                        func.sum(TrainingDataset.gmv),
                        func.avg(TrainingDataset.roas),
                        func.count(TrainingDataset.id)
                    ).first()
                    
                    total_profit = float(res[0] or 0.0)
                    total_gmv = float(res[1] or 0.0)
                    avg_roas = float(res[2] or 0.0)
                    total_records = int(res[3] or 0)
                    
                    top_prods = db.query(
                        TrainingDataset.product_id,
                        func.sum(TrainingDataset.profit),
                        func.sum(TrainingDataset.gmv),
                        func.avg(TrainingDataset.roas)
                    ).group_by(TrainingDataset.product_id).order_by(func.sum(TrainingDataset.profit).desc()).limit(5).all()
                    
                    top_lines = []
                    for idx, tp in enumerate(top_prods, 1):
                        tp_pid, tp_prof, tp_gmv, tp_roas = tp
                        top_lines.append(f"{idx}. 📦 <code>{tp_pid}</code>: <b>{int(tp_prof):,}đ</b> (ROAS: {float(tp_roas or 0):.2f})")
                        
                    profit_text = f"""
💵 <b>BÁO CÁO LỢI NHUẬN HỆ THỐNG ROAS</b>
━━━━━━━━━━━━━━━━━━━
📈 <b>Tổng quan toàn bộ chiến dịch:</b>
• Số ngày-chiến dịch: <b>{total_records}</b> bản ghi
• Tổng doanh thu (GMV): <b>{int(total_gmv):,}đ</b>
• Tổng lợi nhuận ròng: 💸 <b>{int(total_profit):,}đ</b>
• ROAS trung bình: <b>{avg_roas:.2f}x</b>

🏆 <b>Top 5 chiến dịch sinh lời tốt nhất:</b>
{chr(10).join(top_lines) if top_lines else "<i>Chưa có dữ liệu.</i>"}
━━━━━━━━━━━━━━━━━━━
                    """
                    bot.edit_message_text(profit_text, chat_id, message_id, parse_mode="HTML", reply_markup=get_back_button("profit"))
                except Exception as e:
                    bot.edit_message_text(f"❌ Lỗi: {e}", chat_id, message_id, reply_markup=get_back_button("profit"))
                finally:
                    db.close()
                    
            elif data == "cb_profit_by_product":
                user_states[chat_id] = "waiting_for_profit_sp"
                bot.edit_message_text("👉 Vui lòng nhập <b>Mã sản phẩm (Product ID)</b> cần tra cứu lợi nhuận:", chat_id, message_id, parse_mode="HTML", reply_markup=get_back_button("profit"))
                
            elif data == "cb_profit_today":
                import datetime
                today_str = datetime.date.today().strftime("%Y-%m-%d")
                db = get_db_session()
                try:
                    from sqlalchemy import func
                    from .database.models import TrainingDataset
                    res = db.query(
                        func.sum(TrainingDataset.profit),
                        func.sum(TrainingDataset.gmv),
                        func.avg(TrainingDataset.roas),
                        func.count(TrainingDataset.id)
                    ).filter(TrainingDataset.date == today_str).first()
                    
                    if not res or res[3] == 0:
                        bot.edit_message_text(f"📅 <b>LỢI NHUẬN NGÀY: {today_str}</b>\n\n🔍 Chưa có dữ liệu chiến dịch được ghi nhận trong hôm nay.", chat_id, message_id, parse_mode="HTML", reply_markup=get_back_button("profit"))
                    else:
                        profit_text = f"""
📅 <b>LỢI NHUẬN NGÀY HÔM NAY ({today_str})</b>
━━━━━━━━━━━━━━━━━━━
• Số chiến dịch hoạt động: <b>{res[3]}</b>
• Tổng doanh thu (GMV): <b>{int(res[1] or 0):,}đ</b>
• Tổng lợi nhuận ròng: 💸 <b>{int(res[0] or 0):,}đ</b>
• ROAS trung bình: <b>{float(res[2] or 0.0):.2f}x</b>
━━━━━━━━━━━━━━━━━━━
                        """
                        bot.edit_message_text(profit_text, chat_id, message_id, parse_mode="HTML", reply_markup=get_back_button("profit"))
                except Exception as e:
                    bot.edit_message_text(f"❌ Lỗi: {e}", chat_id, message_id, reply_markup=get_back_button("profit"))
                finally:
                    db.close()
                    
            elif data == "cb_profit_week":
                import datetime
                today = datetime.date.today()
                start_week = today - datetime.timedelta(days=today.weekday())
                end_week = start_week + datetime.timedelta(days=6)
                start_week_str = start_week.strftime("%Y-%m-%d")
                end_week_str = end_week.strftime("%Y-%m-%d")
                
                db = get_db_session()
                try:
                    from sqlalchemy import func
                    from .database.models import TrainingDataset
                    res = db.query(
                        func.sum(TrainingDataset.profit),
                        func.sum(TrainingDataset.gmv),
                        func.avg(TrainingDataset.roas),
                        func.count(TrainingDataset.id)
                    ).filter(TrainingDataset.date.between(start_week_str, end_week_str)).first()
                    
                    if not res or res[3] == 0:
                        bot.edit_message_text(f"📅 <b>LỢI NHUẬN TUẦN NÀY</b>\n⏱️ <i>Từ {start_week_str} đến {end_week_str}</i>\n\n🔍 Chưa có dữ liệu chiến dịch được ghi nhận trong tuần này.", chat_id, message_id, parse_mode="HTML", reply_markup=get_back_button("profit"))
                    else:
                        profit_text = f"""
📅 <b>LỢI NHUẬN TUẦN NÀY</b>
⏱️ Từ <code>{start_week_str}</code> đến <code>{end_week_str}</code>
━━━━━━━━━━━━━━━━━━━
• Số chiến dịch hoạt động: <b>{res[3]}</b>
• Tổng doanh thu (GMV): <b>{int(res[1] or 0):,}đ</b>
• Tổng lợi nhuận ròng: 💸 <b>{int(res[0] or 0):,}đ</b>
• ROAS trung bình: <b>{float(res[2] or 0.0):.2f}x</b>
━━━━━━━━━━━━━━━━━━━
                        """
                        bot.edit_message_text(profit_text, chat_id, message_id, parse_mode="HTML", reply_markup=get_back_button("profit"))
                except Exception as e:
                    bot.edit_message_text(f"❌ Lỗi: {e}", chat_id, message_id, reply_markup=get_back_button("profit"))
                finally:
                    db.close()
                    
            elif data == "cb_profit_month":
                import datetime
                today = datetime.date.today()
                month_str = today.strftime("%Y-%m")
                
                db = get_db_session()
                try:
                    from sqlalchemy import func
                    from .database.models import TrainingDataset
                    res = db.query(
                        func.sum(TrainingDataset.profit),
                        func.sum(TrainingDataset.gmv),
                        func.avg(TrainingDataset.roas),
                        func.count(TrainingDataset.id)
                    ).filter(TrainingDataset.date.like(f"{month_str}%")).first()
                    
                    if not res or res[3] == 0:
                        bot.edit_message_text(f"📅 <b>LỢI NHUẬN THÁNG NÀY ({month_str})</b>\n\n🔍 Chưa có dữ liệu chiến dịch được ghi nhận trong tháng này.", chat_id, message_id, parse_mode="HTML", reply_markup=get_back_button("profit"))
                    else:
                        profit_text = f"""
📅 <b>LỢI NHUẬN THÁNG NÀY ({month_str})</b>
━━━━━━━━━━━━━━━━━━━
• Số chiến dịch hoạt động: <b>{res[3]}</b>
• Tổng doanh thu (GMV): <b>{int(res[1] or 0):,}đ</b>
• Tổng lợi nhuận ròng: 💸 <b>{int(res[0] or 0):,}đ</b>
• ROAS trung bình: <b>{float(res[2] or 0.0):.2f}x</b>
━━━━━━━━━━━━━━━━━━━
                        """
                        bot.edit_message_text(profit_text, chat_id, message_id, parse_mode="HTML", reply_markup=get_back_button("profit"))
                except Exception as e:
                    bot.edit_message_text(f"❌ Lỗi: {e}", chat_id, message_id, reply_markup=get_back_button("profit"))
                finally:
                    db.close()
                    
            elif data == "cb_profit_year":
                import datetime
                today = datetime.date.today()
                year_str = today.strftime("%Y")
                
                db = get_db_session()
                try:
                    from sqlalchemy import func
                    from .database.models import TrainingDataset
                    res = db.query(
                        func.sum(TrainingDataset.profit),
                        func.sum(TrainingDataset.gmv),
                        func.avg(TrainingDataset.roas),
                        func.count(TrainingDataset.id)
                    ).filter(TrainingDataset.date.like(f"{year_str}%")).first()
                    
                    if not res or res[3] == 0:
                        bot.edit_message_text(f"📅 <b>LỢI NHUẬN NĂM NÀY ({year_str})</b>\n\n🔍 Chưa có dữ liệu chiến dịch được ghi nhận trong năm nay.", chat_id, message_id, parse_mode="HTML", reply_markup=get_back_button("profit"))
                    else:
                        profit_text = f"""
📅 <b>LỢI NHUẬN NĂM NÀY ({year_str})</b>
━━━━━━━━━━━━━━━━━━━
• Số chiến dịch hoạt động: <b>{res[3]}</b>
• Tổng doanh thu (GMV): <b>{int(res[1] or 0):,}đ</b>
• Tổng lợi nhuận ròng: 💸 <b>{int(res[0] or 0):,}đ</b>
• ROAS trung bình: <b>{float(res[2] or 0.0):.2f}x</b>
━━━━━━━━━━━━━━━━━━━
                        """
                        bot.edit_message_text(profit_text, chat_id, message_id, parse_mode="HTML", reply_markup=get_back_button("profit"))
                except Exception as e:
                    bot.edit_message_text(f"❌ Lỗi: {e}", chat_id, message_id, reply_markup=get_back_button("profit"))
                finally:
                    db.close()
            
            # 3. Product Actions
            elif data == "cb_product_search":
                user_states[chat_id] = "waiting_for_search"
                bot.edit_message_text("🔎 Vui lòng nhập <b>tên hoặc từ khóa sản phẩm</b> cần tìm kiếm:", chat_id, message_id, parse_mode="HTML", reply_markup=get_back_button("products"))
                
            elif data == "cb_products_list":
                db = get_db_session()
                try:
                    products = db.query(RawProduct).order_by(RawProduct.id.desc()).limit(5).all()
                    if not products:
                        bot.edit_message_text("📭 Kho dữ liệu trống.", chat_id, message_id, reply_markup=get_back_button("products"))
                        return
                    
                    response_lines = ["📦 <b>SẢN PHẨM MỚI CÀO GẦN ĐÂY:</b>\n"]
                    markup = InlineKeyboardMarkup()
                    for idx, prod in enumerate(products, 1):
                        line = f"{idx}. {prod.title[:45]}...\n   └ ID: <code>{prod.product_id}</code>"
                        response_lines.append(line)
                    markup.row(InlineKeyboardButton("🔙 Quay lại Menu", callback_data="cb_back_products"))
                    bot.edit_message_text("\n".join(response_lines), chat_id, message_id, parse_mode="HTML", reply_markup=markup)
                except Exception as e:
                    bot.edit_message_text(f"❌ Lỗi: {e}", chat_id, message_id, reply_markup=get_back_button("products"))
                finally:
                    db.close()
                    
            elif data == "cb_products_best":
                db = get_db_session()
                try:
                    products = db.query(RawProduct).filter(RawProduct.sold_count.isnot(None)).order_by(RawProduct.sold_count.desc()).limit(5).all()
                    if not products:
                        products = db.query(RawProduct).order_by(RawProduct.id.desc()).limit(5).all()
                    
                    response_lines = ["🔥 <b>TOP SẢN PHẨM BÁN CHẠY NHẤT:</b>\n"]
                    markup = InlineKeyboardMarkup()
                    for idx, prod in enumerate(products, 1):
                        sold_val = prod.sold_count or 0
                        response_lines.append(f"{idx}. {prod.title[:45]}...\n   └ Đã bán: <b>{sold_val:,}</b> | ID: <code>{prod.product_id}</code>")
                    markup.row(InlineKeyboardButton("🔙 Quay lại Menu", callback_data="cb_back_products"))
                    bot.edit_message_text("\n".join(response_lines), chat_id, message_id, parse_mode="HTML", reply_markup=markup)
                except Exception as e:
                    bot.edit_message_text(f"❌ Lỗi: {e}", chat_id, message_id, reply_markup=get_back_button("products"))
                finally:
                    db.close()
                    
            elif data == "cb_products_rated":
                db = get_db_session()
                try:
                    products = db.query(RawProduct).filter(RawProduct.rating_star.isnot(None)).order_by(RawProduct.rating_star.desc()).limit(5).all()
                    if not products:
                        products = db.query(RawProduct).order_by(RawProduct.id.desc()).limit(5).all()
                        
                    response_lines = ["⭐ <b>TOP SẢN PHẨM ĐÁNH GIÁ CAO:</b>\n"]
                    markup = InlineKeyboardMarkup()
                    for idx, prod in enumerate(products, 1):
                        rating_val = prod.rating_star or 0.0
                        response_lines.append(f"{idx}. {prod.title[:45]}...\n   └ Đánh giá: <b>{rating_val:.1f}⭐</b> | ID: <code>{prod.product_id}</code>")
                    markup.row(InlineKeyboardButton("🔙 Quay lại Menu", callback_data="cb_back_products"))
                    bot.edit_message_text("\n".join(response_lines), chat_id, message_id, parse_mode="HTML", reply_markup=markup)
                except Exception as e:
                    bot.edit_message_text(f"❌ Lỗi: {e}", chat_id, message_id, reply_markup=get_back_button("products"))
                finally:
                    db.close()
            
            # 4. Crawl Actions
            elif data == "cb_crawl_by_url":
                user_states[chat_id] = "waiting_for_crawl_url"
                bot.edit_message_text("🔗 Vui lòng gửi đường dẫn <b>URL Shop Shopee</b> để bắt đầu cào:\n\n<i>Ví dụ: https://shopee.vn/byjane.hn</i>", chat_id, message_id, parse_mode="HTML", reply_markup=get_back_button("crawl"))
                
            elif data == "cb_crawl_tab_run":
                bot.send_message(chat_id, "🤖 <b>Bắt đầu cào sản phẩm từ tab Shopee hoạt động...</b>\n⚙️ <i>Đang kết nối qua Chrome Debug 9222...</i>", parse_mode="HTML")
                
                def run_crawl_active_thread():
                    db = get_db_session()
                    try:
                        def log_to_user(msg):
                            clean_msg = msg.strip()
                            if not clean_msg:
                                return
                            keywords = ["BẮT ĐẦU", "HOÀN THÀNH", "Tổng cộng", "Đã lưu", "Lỗi", "Không", "debug", "Bỏ qua", "Chrome", "CDP"]
                            emojis = ["❌", "⚠️", "⏭️", "✅", "🌐", "📝", "🛒", "🤖", "📋"]
                            if any(kw in clean_msg for kw in keywords) or any(clean_msg.startswith(em) for em in emojis):
                                bot.send_message(chat_id, f"📝 <i>{clean_msg}</i>", parse_mode="HTML")
                                
                        total = crawl_active_shopee_tab(db, log_callback=log_to_user)
                        bot.send_message(chat_id, f"✅ <b>HOÀN THÀNH CÀO TAB HOẠT ĐỘNG!</b>\n🛒 Thêm mới thành công: <b>{total}</b> sản phẩm vào cơ sở dữ liệu.", parse_mode="HTML", reply_markup=get_back_button("crawl"))
                    except Exception as ex:
                        bot.send_message(chat_id, f"❌ <b>Lỗi cào sản phẩm:</b> <code>{str(ex)}</code>", parse_mode="HTML", reply_markup=get_back_button("crawl"))
                    finally:
                        db.close()
                        
                threading.Thread(target=run_crawl_active_thread, daemon=True).start()
                
            # 5. Marketing/AI Actions
            elif data == "cb_run_seo_prompt":
                user_states[chat_id] = "waiting_for_seo_id"
                bot.edit_message_text("🏷️ Vui lòng nhập <b>Mã sản phẩm (Product ID)</b> cần tối ưu SEO bằng AI Gemini:", chat_id, message_id, parse_mode="HTML", reply_markup=get_back_button("marketing"))
                
            elif data == "cb_run_fb_prompt":
                user_states[chat_id] = "waiting_for_fb_id"
                bot.edit_message_text("📱 Vui lòng nhập <b>Mã sản phẩm (Product ID)</b> cần soạn bài viết quảng cáo Facebook:", chat_id, message_id, parse_mode="HTML", reply_markup=get_back_button("marketing"))
                
            elif data == "cb_run_publish":
                bot.send_message(chat_id, "🚀 <b>Đang quét hàng đợi bài viết Facebook...</b>\n⚙️ <i>Đang đăng bài...</i>", parse_mode="HTML")
                
                db = get_db_session()
                try:
                    posts = repository.get_all_fb_posts(db)
                    pending_posts = [p for p in posts if p.status == "Pending"]
                    
                    if not pending_posts:
                        bot.send_message(chat_id, "ℹ️ Không tìm thấy bài viết nào có trạng thái <b>Pending</b> trong hàng đợi.", parse_mode="HTML", reply_markup=get_back_button("marketing"))
                        return
                        
                    post_to_publish = pending_posts[0]
                    product_id = post_to_publish.product_id
                    
                    raw_prod = repository.get_raw_product_by_product_id(db, product_id)
                    image_urls = raw_prod.images if raw_prod else []
                    
                    repository.update_fb_post_status(db, product_id, "Publishing")
                    
                    success, msg = publish_to_facebook(post_to_publish.caption, image_urls)
                    if success:
                        repository.update_fb_post_status(db, product_id, "Posted")
                        bot.send_message(chat_id, f"🎉 <b>ĐĂNG BÀI THÀNH CÔNG!</b>\n📦 Sản phẩm ID: <code>{product_id}</code>\n📢 Kết quả: <code>{msg}</code>", parse_mode="HTML", reply_markup=get_back_button("marketing"))
                    else:
                        repository.update_fb_post_status(db, product_id, "Failed")
                        bot.send_message(chat_id, f"❌ <b>ĐĂNG BÀI THẤT BẠI!</b>\n📦 Sản phẩm ID: <code>{product_id}</code>\n⚠️ Lỗi: <code>{msg}</code>", parse_mode="HTML", reply_markup=get_back_button("marketing"))
                except Exception as e:
                    bot.send_message(chat_id, f"❌ <b>Lỗi tiến trình:</b> <code>{str(e)}</code>", parse_mode="HTML", reply_markup=get_back_button("marketing"))
                finally:
                    db.close()
            
            # Quick actions with specific IDs
            elif data.startswith("seo_"):
                product_id = data.split("_")[1]
                run_seo_action_direct(chat_id, product_id)
                
            elif data.startswith("fb_"):
                product_id = data.split("_")[1]
                run_fb_action_direct(chat_id, product_id)

        # Helper actions for inline buttons
        def run_seo_action_direct(chat_id, product_id):
            bot.send_message(chat_id, f"🤖 Đang khởi chạy tối ưu hóa SEO bằng AI cho sản phẩm ID <code>{product_id}</code>...", parse_mode="HTML")
            db = get_db_session()
            try:
                raw_prod = repository.get_raw_product_by_product_id(db, product_id)
                if not raw_prod:
                    bot.send_message(chat_id, f"❌ Không tìm thấy sản phẩm có ID: <code>{product_id}</code> trong cơ sở dữ liệu.", parse_mode="HTML", reply_markup=get_back_button("marketing"))
                    return
                    
                seo_data = run_seo_generator(raw_prod.title, raw_prod.description, raw_prod.brand)
                seo_prod = repository.create_or_update_seo_product(db, product_id, seo_data)
                
                score = seo_prod.seo_score or 0
                num_blocks = int(round(score / 10))
                progress_bar = "█" * num_blocks + "░" * (10 - num_blocks)
                
                sec_kw_list = seo_prod.secondary_keywords or []
                if isinstance(sec_kw_list, str):
                    try:
                        import json
                        sec_kw_list = json.loads(sec_kw_list)
                    except:
                        sec_kw_list = [sec_kw_list]
                sec_kw_text = ", ".join([f"#{kw.strip()}" for kw in sec_kw_list if kw]) or "Không có"
                
                usp_list = seo_prod.usp or []
                if isinstance(usp_list, str):
                    try:
                        import json
                        usp_list = json.loads(usp_list)
                    except:
                        usp_list = [usp_list]
                usp_text = "\n".join([f"• 🌟 {item.strip()}" for item in usp_list if item]) or "• Không có"
                
                seo_response = f"""
✅ <b>TỐI ƯU HÓA SEO THÀNH CÔNG!</b>
━━━━━━━━━━━━━━━━━━━
📦 <b>Sản phẩm:</b> {raw_prod.title}
🆔 <b>Mã sản phẩm:</b> <code>{product_id}</code>

📈 <b>Điểm số SEO:</b>
<code>[{progress_bar}] {score}/100</code>

🏷️ <b>Tiêu đề SEO mới:</b>
👉 <b>{seo_prod.seo_title}</b>

🔑 <b>Từ khóa chính:</b> <code>{seo_prod.main_keyword}</code>
🏷️ <b>Từ khóa phụ:</b> <i>{sec_kw_text}</i>

🌟 <b>Lợi thế bán hàng độc nhất (USP):</b>
{usp_text}

📝 <b>Mô tả Meta (Meta Description):</b>
{seo_prod.meta_description}
━━━━━━━━━━━━━━━━━━━
                """
                
                markup = InlineKeyboardMarkup()
                markup.row(InlineKeyboardButton("📱 Soạn bài Facebook ngay", callback_data=f"fb_{product_id}"))
                markup.row(InlineKeyboardButton("🔙 Quay lại Menu", callback_data="cb_back_marketing"))
                
                bot.send_message(chat_id, seo_response, parse_mode="HTML", reply_markup=markup)
            except Exception as e:
                bot.send_message(chat_id, f"❌ Lỗi khi tối ưu hóa SEO: <code>{str(e)}</code>", parse_mode="HTML", reply_markup=get_back_button("marketing"))
            finally:
                db.close()

        def run_fb_action_direct(chat_id, product_id):
            bot.send_message(chat_id, f"📝 Đang khởi tạo bài đăng Facebook cho sản phẩm <code>{product_id}</code>...", parse_mode="HTML")
            db = get_db_session()
            try:
                raw_prod = repository.get_raw_product_by_product_id(db, product_id)
                seo_prod = repository.get_seo_product_by_product_id(db, product_id)
                if not seo_prod or not raw_prod:
                    markup = InlineKeyboardMarkup()
                    markup.row(InlineKeyboardButton("🏷️ Chạy SEO trước", callback_data=f"seo_{product_id}"))
                    markup.row(InlineKeyboardButton("🔙 Quay lại Menu", callback_data="cb_back_marketing"))
                    bot.send_message(chat_id, f"⚠️ Sản phẩm chưa được tối ưu SEO. Vui lòng chạy tối ưu hóa SEO trước khi tạo bài đăng Facebook!", parse_mode="HTML", reply_markup=markup)
                    return
                    
                fb_data = generate_fb_content(
                    raw_prod.title, seo_prod.seo_title, seo_prod.meta_description,
                    seo_prod.main_keyword, seo_prod.secondary_keywords, seo_prod.usp
                )
                fb_post = repository.create_or_update_fb_post(db, product_id, fb_data)
                
                img_urls = raw_prod.images or []
                if isinstance(img_urls, str):
                    try:
                        import json
                        img_urls = json.loads(img_urls)
                    except:
                        img_urls = [img_urls] if img_urls else []
                img_count = len(img_urls)
                
                caption = fb_post.caption or ""
                preview_length = 800
                caption_preview = caption if len(caption) <= preview_length else f"{caption[:preview_length]}...\n\n<i>[Còn tiếp...]</i>"
                
                fb_response = f"""
✅ <b>ĐÃ THÊM BÀI VIẾT VÀO HÀNG ĐỢI FACEBOOK!</b>
━━━━━━━━━━━━━━━━━━━
🆔 <b>Mã sản phẩm:</b> <code>{product_id}</code>
📊 <b>Trạng thái:</b> ⏳ <b>Pending</b> (Chờ duyệt đăng)
🖼️ <b>Hình ảnh đính kèm:</b> <b>{img_count}</b> ảnh sẵn sàng

📝 <b>Nội dung bài viết mẫu:</b>
───────────────────
{caption_preview}
───────────────────
━━━━━━━━━━━━━━━━━━━
                """
                markup = InlineKeyboardMarkup()
                markup.row(InlineKeyboardButton("🚀 Đăng lên Fanpage ngay", callback_data="cb_run_publish"))
                markup.row(InlineKeyboardButton("🔙 Quay lại Menu", callback_data="cb_back_marketing"))
                bot.send_message(chat_id, fb_response, parse_mode="HTML", reply_markup=markup)
            except Exception as e:
                bot.send_message(chat_id, f"❌ Lỗi khi sinh bài đăng Facebook: <code>{str(e)}</code>", parse_mode="HTML", reply_markup=get_back_button("marketing"))
            finally:
                db.close()

        def perform_search_interactive(message, keyword: str):
            chat_id = message.chat.id
            db = get_db_session()
            try:
                keyword_clean = keyword.strip()
                if not keyword_clean:
                    bot.send_message(chat_id, "❌ Từ khóa tìm kiếm không được để trống.", reply_markup=get_back_button("products"))
                    return
                
                from sqlalchemy import or_
                results = db.query(RawProduct).filter(
                    or_(
                        RawProduct.title.like(f"%{keyword_clean}%"),
                        RawProduct.product_id.like(f"%{keyword_clean}%")
                    )
                ).limit(5).all()
                
                if not results:
                    bot.send_message(chat_id, f"🔍 Không tìm thấy sản phẩm nào khớp với từ khóa: <b>{keyword_clean}</b>", parse_mode="HTML", reply_markup=get_back_button("products"))
                    return
                
                response_lines = [
                    f"🔍 <b>KẾT QUẢ TÌM KIẾM CHO:</b> <i>{keyword_clean}</i>\n",
                ]
                
                markup = InlineKeyboardMarkup()
                for idx, prod in enumerate(results, 1):
                    line = f"{idx}. {prod.title[:45]}...\n   └ ID: <code>{prod.product_id}</code>"
                    response_lines.append(line)
                
                markup.row(InlineKeyboardButton("🔙 Quay lại Menu", callback_data="cb_back_products"))
                bot.send_message(chat_id, "\n".join(response_lines), parse_mode="HTML", reply_markup=markup)
            except Exception as e:
                bot.send_message(chat_id, f"❌ Lỗi trong quá trình tìm kiếm: <code>{str(e)}</code>", parse_mode="HTML", reply_markup=get_back_button("products"))
            finally:
                db.close()

        def perform_profit_sp_interactive(chat_id, product_id):
            db = get_db_session()
            try:
                from sqlalchemy import func
                from .database.models import TrainingDataset
                pid = product_id.strip()
                res = db.query(
                    func.sum(TrainingDataset.profit),
                    func.sum(TrainingDataset.gmv),
                    func.avg(TrainingDataset.roas),
                    func.count(TrainingDataset.id)
                ).filter(TrainingDataset.product_id == pid).first()
                
                if not res or res[3] == 0:
                    bot.send_message(chat_id, f"🔍 Không tìm thấy dữ liệu chiến dịch của sản phẩm: <code>{pid}</code>", parse_mode="HTML", reply_markup=get_back_button("profit"))
                    return
                    
                profit_text = f"""
📦 <b>BÁO CÁO LỢI NHUẬN SẢN PHẨM:</b>
🆔 Mã SP: <code>{pid}</code>
━━━━━━━━━━━━━━━━━━━
• Số ngày chạy chiến dịch: <b>{res[3]}</b> ngày
• Tổng doanh thu (GMV): <b>{int(res[1] or 0):,}đ</b>
• Tổng lợi nhuận: 💸 <b>{int(res[0] or 0):,}đ</b>
• ROAS trung bình: <b>{float(res[2] or 0.0):.2f}x</b>
━━━━━━━━━━━━━━━━━━━
                """
                
                raw_prod = repository.get_raw_product_by_product_id(db, pid)
                markup = InlineKeyboardMarkup()
                if raw_prod:
                    markup.row(
                        InlineKeyboardButton("🏷️ Tối ưu SEO", callback_data=f"seo_{pid}"),
                        InlineKeyboardButton("📱 Viết bài FB", callback_data=f"fb_{pid}")
                    )
                markup.row(InlineKeyboardButton("🔙 Quay lại Menu Lợi nhuận", callback_data="cb_back_profit"))
                bot.send_message(chat_id, profit_text, parse_mode="HTML", reply_markup=markup)
            except Exception as e:
                bot.send_message(chat_id, f"❌ Lỗi: {e}", reply_markup=get_back_button("profit"))
            finally:
                db.close()

        def perform_crawl_url_interactive(chat_id, url):
            url_clean = url.strip()
            if "shopee.vn" not in url_clean:
                bot.send_message(chat_id, "❌ URL không hợp lệ! Vui lòng cung cấp chính xác đường dẫn cửa hàng Shopee (shopee.vn).", reply_markup=get_back_button("crawl"))
                return
                
            bot.send_message(chat_id, f"🤖 <b>Bắt đầu tiến trình cào dữ liệu:</b>\n🔗 Cửa hàng: <code>{url_clean}</code>\n⚙️ <i>Kết nối tự động qua Chrome Debug (cổng 9222)...</i>", parse_mode="HTML")
            
            def run_crawl_thread():
                db = get_db_session()
                try:
                    def log_to_user(msg):
                        clean_msg = msg.strip()
                        if not clean_msg:
                            return
                        keywords = ["BẮT ĐẦU", "HOÀN THÀNH", "Tổng cộng", "Đã lưu", "Lỗi", "Không", "debug", "Bỏ qua", "Chrome", "CDP"]
                        emojis = ["❌", "⚠️", "⏭️", "✅", "🌐", "📝", "🛒", "🤖", "📋"]
                        if any(kw in clean_msg for kw in keywords) or any(clean_msg.startswith(em) for em in emojis):
                            bot.send_message(chat_id, f"📝 <i>{clean_msg}</i>", parse_mode="HTML")
                            
                    total = crawl_shopee_shop_products(url_clean, db, log_callback=log_to_user)
                    bot.send_message(chat_id, f"✅ <b>HOÀN THÀNH CÀO CỬA HÀNG!</b>\n🛒 Thêm mới thành công: <b>{total}</b> sản phẩm vào cơ sở dữ liệu.", parse_mode="HTML", reply_markup=get_back_button("crawl"))
                except Exception as ex:
                    bot.send_message(chat_id, f"❌ <b>Lỗi trong tiến trình cào:</b> <code>{str(ex)}</code>", parse_mode="HTML", reply_markup=get_back_button("crawl"))
                finally:
                    db.close()
                    
            threading.Thread(target=run_crawl_thread, daemon=True).start()


        # Command status
        @bot.message_handler(commands=['status'])
        def send_status(message):
            db = get_db_session()
            try:
                raw_count = len(repository.get_all_raw_products(db))
                seo_count = len(repository.get_all_seo_products(db))
                fb_posts = repository.get_all_fb_posts(db)
                
                pending = len([p for p in fb_posts if p.status == "Pending"])
                posted = len([p for p in fb_posts if p.status == "Posted"])
                failed = len([p for p in fb_posts if p.status == "Failed"])
                
                status_text = f"""
📊 <b>BÁO CÁO TRẠNG THÁI HỆ THỐNG</b>
━━━━━━━━━━━━━━━━━━━
🛒 <b>Dữ liệu sản phẩm:</b>
• Tổng sản phẩm đã cào (Raw DB): <b>{raw_count}</b> sản phẩm
• Đã tối ưu hóa SEO bằng AI: <b>{seo_count}</b> sản phẩm
• Tỷ lệ phủ SEO: <b>{((seo_count / raw_count * 100) if raw_count > 0 else 0):.1f}%</b>

📈 <b>Hàng đợi bài đăng Facebook:</b>
• Đang chờ duyệt (Pending): ⏳ <b>{pending}</b> bài viết
• Đã đăng thành công (Posted): ✅ <b>{posted}</b> bài viết
• Đăng thất bại (Failed): ❌ <b>{failed}</b> bài viết
• Tổng số bài viết trong queue: 📋 <b>{len(fb_posts)}</b>
━━━━━━━━━━━━━━━━━━━
👉 <i>Để tìm kiếm sản phẩm và lấy ID, hãy gửi trực tiếp từ khóa tìm kiếm cho Bot.</i>
                """
                bot.reply_to(message, status_text, parse_mode="HTML")
            except Exception as e:
                bot.reply_to(message, f"❌ Lỗi truy vấn cơ sở dữ liệu: <code>{str(e)}</code>", parse_mode="HTML")
            finally:
                db.close()

        # Command profit / loinhuan
        @bot.message_handler(commands=['profit', 'loinhuan'])
        def handle_profit(message):
            db = get_db_session()
            try:
                from sqlalchemy import func
                from .database.models import TrainingDataset
                
                text = message.text.split()
                
                if len(text) == 1:
                    # Xem tổng hợp lợi nhuận chung
                    res = db.query(
                        func.sum(TrainingDataset.profit),
                        func.sum(TrainingDataset.gmv),
                        func.avg(TrainingDataset.roas),
                        func.count(TrainingDataset.id)
                    ).first()
                    
                    total_profit = float(res[0] or 0.0)
                    total_gmv = float(res[1] or 0.0)
                    avg_roas = float(res[2] or 0.0)
                    total_records = int(res[3] or 0)
                    
                    # Top products by profit
                    top_prods = db.query(
                        TrainingDataset.product_id,
                        func.sum(TrainingDataset.profit),
                        func.sum(TrainingDataset.gmv),
                        func.avg(TrainingDataset.roas)
                    ).group_by(TrainingDataset.product_id).order_by(func.sum(TrainingDataset.profit).desc()).limit(5).all()
                    
                    top_lines = []
                    for idx, tp in enumerate(top_prods, 1):
                        tp_pid, tp_prof, tp_gmv, tp_roas = tp
                        top_lines.append(f"{idx}. 📦 <code>{tp_pid}</code>: <b>{int(tp_prof):,}đ</b> (GMV: {int(tp_gmv):,}đ, ROAS: {float(tp_roas or 0):.2f})")
                        
                    status_text = f"""
💵 <b>BÁO CÁO LỢI NHUẬN HỆ THỐNG ROAS</b>
━━━━━━━━━━━━━━━━━━━
📈 <b>Tổng quan toàn bộ chiến dịch:</b>
• Số ngày-chiến dịch ghi nhận: <b>{total_records}</b> bản ghi
• Tổng doanh thu (GMV): <b>{int(total_gmv):,}đ</b>
• Tổng lợi nhuận ròng: 💸 <b>{int(total_profit):,}đ</b>
• ROAS trung bình: <b>{avg_roas:.2f}x</b>

🏆 <b>Top 5 chiến dịch sinh lời tốt nhất:</b>
{chr(10).join(top_lines) if top_lines else "<i>Chưa có dữ liệu.</i>"}
━━━━━━━━━━━━━━━━━━━
💡 <b>Cú pháp tra cứu chi tiết:</b>
• Theo sản phẩm: <code>/profit sp [Product_ID]</code>
• Theo ngày cụ thể: <code>/profit date [YYYY-MM-DD]</code>
• Theo khoảng ngày: <code>/profit range [YYYY-MM-DD] [YYYY-MM-DD]</code>
                    """
                    bot.reply_to(message, status_text, parse_mode="HTML")
                    return
                
                sub_cmd = text[1].lower()
                if sub_cmd in ["sp", "sanpham", "product"]:
                    if len(text) < 3:
                        bot.reply_to(message, "❌ Vui lòng cung cấp mã sản phẩm. Cú pháp: <code>/profit sp [Product_ID]</code>", parse_mode="HTML")
                        return
                    pid = text[2]
                    res = db.query(
                        func.sum(TrainingDataset.profit),
                        func.sum(TrainingDataset.gmv),
                        func.avg(TrainingDataset.roas),
                        func.count(TrainingDataset.id)
                    ).filter(TrainingDataset.product_id == pid).first()
                    
                    if not res or res[3] == 0:
                        bot.reply_to(message, f"🔍 Không tìm thấy dữ liệu chiến dịch của sản phẩm: <code>{pid}</code>", parse_mode="HTML")
                        return
                        
                    bot.reply_to(message, f"""
📦 <b>BÁO CÁO LỢI NHUẬN SẢN PHẨM:</b>
🆔 Mã SP: <code>{pid}</code>
━━━━━━━━━━━━━━━━━━━
• Số ngày chạy chiến dịch: <b>{res[3]}</b> ngày
• Tổng doanh thu (GMV): <b>{int(res[1] or 0):,}đ</b>
• Tổng lợi nhuận: 💸 <b>{int(res[0] or 0):,}đ</b>
• ROAS trung bình: <b>{float(res[2] or 0.0):.2f}x</b>
                    """, parse_mode="HTML")
                    
                elif sub_cmd in ["date", "ngay"]:
                    if len(text) < 3:
                        bot.reply_to(message, "❌ Vui lòng cung cấp ngày. Cú pháp: <code>/profit date [YYYY-MM-DD]</code>", parse_mode="HTML")
                        return
                    target_date = text[2]
                    res = db.query(
                        func.sum(TrainingDataset.profit),
                        func.sum(TrainingDataset.gmv),
                        func.avg(TrainingDataset.roas),
                        func.count(TrainingDataset.id)
                    ).filter(TrainingDataset.date == target_date).first()
                    
                    if not res or res[3] == 0:
                        bot.reply_to(message, f"🔍 Không tìm thấy dữ liệu chiến dịch vào ngày: <code>{target_date}</code>", parse_mode="HTML")
                        return
                        
                    bot.reply_to(message, f"""
📅 <b>BÁO CÁO LỢI NHUẬN NGÀY: {target_date}</b>
━━━━━━━━━━━━━━━━━━━
• Số chiến dịch hoạt động: <b>{res[3]}</b>
• Tổng doanh thu (GMV): <b>{int(res[1] or 0):,}đ</b>
• Tổng lợi nhuận: 💸 <b>{int(res[0] or 0):,}đ</b>
• ROAS trung bình: <b>{float(res[2] or 0.0):.2f}x</b>
                    """, parse_mode="HTML")
                    
                elif sub_cmd in ["range", "khoang"]:
                    if len(text) < 4:
                        bot.reply_to(message, "❌ Vui lòng cung cấp khoảng ngày. Cú pháp: <code>/profit range [YYYY-MM-DD] [YYYY-MM-DD]</code>", parse_mode="HTML")
                        return
                    start_date, end_date = text[2], text[3]
                    res = db.query(
                        func.sum(TrainingDataset.profit),
                        func.sum(TrainingDataset.gmv),
                        func.avg(TrainingDataset.roas),
                        func.count(TrainingDataset.id)
                    ).filter(TrainingDataset.date.between(start_date, end_date)).first()
                    
                    if not res or res[3] == 0:
                        bot.reply_to(message, f"🔍 Không tìm thấy dữ liệu chiến dịch trong khoảng: <code>{start_date}</code> đến <code>{end_date}</code>", parse_mode="HTML")
                        return
                        
                    bot.reply_to(message, f"""
📅 <b>BÁO CÁO LỢI NHUẬN KHOẢNG THỜI GIAN:</b>
⏱️ Từ <code>{start_date}</code> đến <code>{end_date}</code>
━━━━━━━━━━━━━━━━━━━
• Tổng số ngày-chiến dịch: <b>{res[3]}</b>
• Tổng doanh thu (GMV): <b>{int(res[1] or 0):,}đ</b>
• Tổng lợi nhuận: 💸 <b>{int(res[0] or 0):,}đ</b>
• ROAS trung bình: <b>{float(res[2] or 0.0):.2f}x</b>
                    """, parse_mode="HTML")
                else:
                    bot.reply_to(message, "❌ Cú pháp không hợp lệ. Gõ <code>/profit</code> để xem hướng dẫn sử dụng.", parse_mode="HTML")
            except Exception as e:
                bot.reply_to(message, f"❌ Lỗi truy vấn lợi nhuận: <code>{str(e)}</code>", parse_mode="HTML")
            finally:
                db.close()

        # Command search <keyword>
        @bot.message_handler(commands=['search'])
        def handle_search(message):
            text = message.text.split()
            if len(text) < 2:
                bot.reply_to(message, "❌ Vui lòng nhập từ khóa tìm kiếm! Cú pháp: <code>/search &lt;tên sản phẩm&gt;</code>", parse_mode="HTML")
                return
                
            keyword = " ".join(text[1:])
            perform_search(message, keyword)

        # Command products
        @bot.message_handler(commands=['products'])
        def handle_products(message):
            db = get_db_session()
            try:
                products = db.query(RawProduct).order_by(RawProduct.id.desc()).limit(10).all()
                if not products:
                    bot.reply_to(message, "📭 <i>Kho dữ liệu hiện chưa có sản phẩm nào. Bạn hãy chạy <code>/crawltab</code> hoặc <code>/crawl &lt;URL&gt;</code> để thêm sản phẩm nhé!</i>", parse_mode="HTML")
                    return
                
                response_lines = [
                    "📦 <b>DANH SÁCH SẢN PHẨM MỚI CÀO CẬP NHẬT</b>",
                    "Dưới đây là 10 sản phẩm vừa được đưa vào hệ thống:",
                    "━━━━━━━━━━━━━━━━━━━"
                ]
                
                for idx, prod in enumerate(products, 1):
                    price_str = f"{int(prod.price):,}₫".replace(",", ".") if prod.price else (prod.price_text or "Chưa rõ giá")
                    rating_str = f"⭐ {prod.rating_star:.1f}" if prod.rating_star else "⭐ Chưa có"
                    sold_str = f"Đã bán {prod.sold_count:,}" if prod.sold_count else "Chưa bán"
                    
                    line = f"{idx}. <b>{prod.title[:50]}...</b>\n"
                    line += f"   💵 <code>{price_str}</code> | {rating_str} | 📦 {sold_str}\n"
                    line += f"   🆔 ID: <code>{prod.product_id}</code>\n"
                    if prod.url:
                        line += f"   🔗 <a href='{prod.url}'>Xem sản phẩm Shopee</a>\n"
                    response_lines.append(line)
                    
                response_lines.append("━━━━━━━━━━━━━━━━━━━")
                response_lines.append("💡 <i>Sao chép ID sản phẩm và gõ <code>/seo &lt;ID&gt;</code> để tối ưu hóa SEO bằng AI.</i>")
                bot.reply_to(message, "\n".join(response_lines), parse_mode="HTML", disable_web_page_preview=True)
            except Exception as e:
                bot.reply_to(message, f"❌ Lỗi khi lấy danh sách sản phẩm: <code>{str(e)}</code>", parse_mode="HTML")
            finally:
                db.close()

        # Command bestselling
        @bot.message_handler(commands=['bestselling', 'best'])
        def handle_bestselling(message):
            db = get_db_session()
            try:
                products = db.query(RawProduct).filter(RawProduct.sold_count.isnot(None)).order_by(RawProduct.sold_count.desc()).limit(10).all()
                if not products:
                    products = db.query(RawProduct).order_by(RawProduct.id.desc()).limit(10).all()
                
                if not products:
                    bot.reply_to(message, "📭 <i>Hiện chưa có dữ liệu sản phẩm trong hệ thống.</i>", parse_mode="HTML")
                    return
                
                response_lines = [
                    "🔥 <b>TOP 10 SẢN PHẨM BÁN CHẠY NHẤT TRONG KHO</b>",
                    "Được sắp xếp theo số lượng đã bán ghi nhận từ shop:",
                    "━━━━━━━━━━━━━━━━━━━"
                ]
                
                for idx, prod in enumerate(products, 1):
                    sold_val = prod.sold_count or 0
                    price_str = f"{int(prod.price):,}₫".replace(",", ".") if prod.price else (prod.price_text or "Chưa rõ giá")
                    rating_str = f"⭐ {prod.rating_star:.1f}" if prod.rating_star else "⭐ Chưa có"
                    
                    sales_badge = "🏆" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else "📈"
                    
                    line = f"{sales_badge} {idx}. <b>{prod.title[:55]}...</b>\n"
                    line += f"   🔥 <b>Đã bán: {sold_val:,}</b> sản phẩm\n"
                    line += f"   💵 Giá: <code>{price_str}</code> | Đánh giá: {rating_str}\n"
                    line += f"   🆔 ID: <code>{prod.product_id}</code>\n"
                    response_lines.append(line)
                    
                response_lines.append("━━━━━━━━━━━━━━━━━━━")
                response_lines.append("💡 <i>Nhấp vào mã ID ở trên để copy và chạy <code>/seo [ID]</code> ngay!</i>")
                bot.reply_to(message, "\n".join(response_lines), parse_mode="HTML", disable_web_page_preview=True)
            except Exception as e:
                bot.reply_to(message, f"❌ Lỗi khi lấy danh sách bán chạy: <code>{str(e)}</code>", parse_mode="HTML")
            finally:
                db.close()

        # Command toprate
        @bot.message_handler(commands=['toprate', 'rate'])
        def handle_toprate(message):
            db = get_db_session()
            try:
                products = db.query(RawProduct).filter(RawProduct.rating_star.isnot(None)).order_by(RawProduct.rating_star.desc(), RawProduct.sold_count.desc()).limit(10).all()
                if not products:
                    products = db.query(RawProduct).order_by(RawProduct.id.desc()).limit(10).all()
                    
                if not products:
                    bot.reply_to(message, "📭 <i>Hiện chưa có dữ liệu sản phẩm trong hệ thống.</i>", parse_mode="HTML")
                    return
                
                response_lines = [
                    "⭐️ <b>TOP 10 SẢN PHẨM CÓ ĐÁNH GIÁ CAO NHẤT</b>",
                    "Được sắp xếp theo điểm đánh giá của khách hàng:",
                    "━━━━━━━━━━━━━━━━━━━"
                ]
                
                for idx, prod in enumerate(products, 1):
                    rating_val = prod.rating_star or 0.0
                    price_str = f"{int(prod.price):,}₫".replace(",", ".") if prod.price else (prod.price_text or "Chưa rõ giá")
                    sold_val = prod.sold_count or 0
                    
                    full_stars = int(rating_val)
                    half_star = 1 if (rating_val - full_stars) >= 0.5 else 0
                    stars_emoji = "⭐" * full_stars + ("✨" if half_star else "")
                    
                    line = f"📍 {idx}. <b>{prod.title[:55]}...</b>\n"
                    line += f"   ⭐️ Đánh giá: <b>{rating_val:.1f}</b> {stars_emoji}\n"
                    line += f"   💵 Giá: <code>{price_str}</code> | Đã bán: {sold_val:,}\n"
                    line += f"   🆔 ID: <code>{prod.product_id}</code>\n"
                    response_lines.append(line)
                    
                response_lines.append("━━━━━━━━━━━━━━━━━━━")
                response_lines.append("💡 <i>Nhấp vào mã ID ở trên để copy và chạy <code>/seo [ID]</code> ngay!</i>")
                bot.reply_to(message, "\n".join(response_lines), parse_mode="HTML", disable_web_page_preview=True)
            except Exception as e:
                bot.reply_to(message, f"❌ Lỗi khi lấy danh sách đánh giá cao: <code>{str(e)}</code>", parse_mode="HTML")
            finally:
                db.close()

        # Command top
        @bot.message_handler(commands=['top', 'top10'])
        def handle_top_summary(message):
            db = get_db_session()
            try:
                best_sellers = db.query(RawProduct).filter(RawProduct.sold_count.isnot(None)).order_by(RawProduct.sold_count.desc()).limit(5).all()
                top_rated = db.query(RawProduct).filter(RawProduct.rating_star.isnot(None)).order_by(RawProduct.rating_star.desc()).limit(5).all()
                
                if not best_sellers and not top_rated:
                    bot.reply_to(message, "📭 <i>Hiện chưa có dữ liệu sản phẩm trong hệ thống.</i>", parse_mode="HTML")
                    return
                
                response_lines = [
                    "🏆 <b>BẢNG VÀNG SẢN PHẨM NỔI BẬT</b> 🏆",
                    "Tổng hợp những sản phẩm xuất sắc nhất trong cơ sở dữ liệu.",
                    "━━━━━━━━━━━━━━━━━━━",
                    "🔥 <b>BÁN CHẠY NHẤT (TOP SALES)</b>"
                ]
                
                if best_sellers:
                    for idx, prod in enumerate(best_sellers, 1):
                        price_str = f"{int(prod.price):,}₫".replace(",", ".") if prod.price else (prod.price_text or "Chưa rõ giá")
                        response_lines.append(f"<b>{idx}. {prod.title[:45]}...</b>")
                        response_lines.append(f"   ├ Đã bán: <b>{prod.sold_count:,}</b> | Giá: <code>{price_str}</code>")
                        response_lines.append(f"   └ ID: <code>{prod.product_id}</code>")
                else:
                    response_lines.append("<i>Chưa có dữ liệu bán hàng.</i>")
                    
                response_lines.append("━━━━━━━━━━━━━━━━━━━")
                response_lines.append("⭐️ <b>ĐÁNH GIÁ CAO NHẤT (TOP RATED)</b>")
                
                if top_rated:
                    for idx, prod in enumerate(top_rated, 1):
                        price_str = f"{int(prod.price):,}₫".replace(",", ".") if prod.price else (prod.price_text or "Chưa rõ giá")
                        response_lines.append(f"<b>{idx}. {prod.title[:45]}...</b>")
                        response_lines.append(f"   ├ Đánh giá: <b>{prod.rating_star:.1f}⭐</b> | Đã bán: <b>{prod.sold_count or 0}</b>")
                        response_lines.append(f"   └ ID: <code>{prod.product_id}</code>")
                else:
                    response_lines.append("<i>Chưa có dữ liệu đánh giá.</i>")
                    
                response_lines.append("━━━━━━━━━━━━━━━━━━━")
                response_lines.append("💡 <i>Dùng lệnh <code>/seo &lt;ID&gt;</code> để bắt đầu tối ưu SEO cho sản phẩm mong muốn.</i>")
                bot.reply_to(message, "\n".join(response_lines), parse_mode="HTML", disable_web_page_preview=True)
            except Exception as e:
                bot.reply_to(message, f"❌ Lỗi khi lấy bảng tổng hợp: <code>{str(e)}</code>", parse_mode="HTML")
            finally:
                db.close()

        # Command crawl <url>
        @bot.message_handler(commands=['crawl'])
        def handle_crawl(message):
            text = message.text.split()
            if len(text) < 2:
                url = "https://shopee.vn/byjane.hn#product_list"
                bot.reply_to(message, "💡 Không nhận được link cửa hàng. Tự động sử dụng cửa hàng mặc định ByJane:\n👉 <code>https://shopee.vn/byjane.hn#product_list</code>", parse_mode="HTML")
            else:
                url = text[1]
                
            if "shopee.vn" not in url:
                bot.reply_to(message, "❌ URL không hợp lệ! Vui lòng cung cấp chính xác đường dẫn cửa hàng Shopee (shopee.vn).", parse_mode="HTML")
                return
                
            bot.reply_to(message, f"🤖 <b>Bắt đầu tiến trình cào dữ liệu:</b>\n🔗 Cửa hàng: <code>{url}</code>\n⚙️ <i>Kết nối tự động qua Chrome Debug (cổng 9222)...</i>", parse_mode="HTML")
            
            def run_crawl_thread():
                db = get_db_session()
                try:
                    def log_to_user(msg):
                        clean_msg = msg.strip()
                        if not clean_msg:
                            return
                        keywords = ["BẮT ĐẦU", "HOÀN THÀNH", "Tổng cộng", "Đã lưu", "Lỗi", "Không", "debug", "Bỏ qua", "Chrome", "CDP"]
                        emojis = ["❌", "⚠️", "⏭️", "✅", "🌐", "📝", "🛒", "🤖", "📋"]
                        if any(kw in clean_msg for kw in keywords) or any(clean_msg.startswith(em) for em in emojis):
                            bot.send_message(message.chat.id, f"📝 <i>{clean_msg}</i>", parse_mode="HTML")
                            
                    total = crawl_shopee_shop_products(url, db, log_callback=log_to_user)
                    bot.send_message(message.chat.id, f"✅ <b>HOÀN THÀNH CÀO CỬA HÀNG!</b>\n🛒 Thêm mới thành công: <b>{total}</b> sản phẩm vào cơ sở dữ liệu.", parse_mode="HTML")
                except Exception as ex:
                    bot.send_message(message.chat.id, f"❌ <b>Lỗi trong tiến trình cào:</b> <code>{str(ex)}</code>", parse_mode="HTML")
                finally:
                    db.close()
                    
            threading.Thread(target=run_crawl_thread, daemon=True).start()

        # Command crawltab
        @bot.message_handler(commands=['crawltab'])
        def handle_crawl_active(message):
            bot.reply_to(message, "🤖 <b>Bắt đầu cào sản phẩm từ tab Shopee hoạt động...</b>\n⚙️ <i>Đang kết nối qua Chrome Debug 9222...</i>", parse_mode="HTML")
            
            def run_crawl_active_thread():
                db = get_db_session()
                try:
                    def log_to_user(msg):
                        clean_msg = msg.strip()
                        if not clean_msg:
                            return
                        keywords = ["BẮT ĐẦU", "HOÀN THÀNH", "Tổng cộng", "Đã lưu", "Lỗi", "Không", "debug", "Bỏ qua", "Chrome", "CDP"]
                        emojis = ["❌", "⚠️", "⏭️", "✅", "🌐", "📝", "🛒", "🤖", "📋"]
                        if any(kw in clean_msg for kw in keywords) or any(clean_msg.startswith(em) for em in emojis):
                            bot.send_message(message.chat.id, f"📝 <i>{clean_msg}</i>", parse_mode="HTML")
                            
                    total = crawl_active_shopee_tab(db, log_callback=log_to_user)
                    bot.send_message(message.chat.id, f"✅ <b>HOÀN THÀNH CÀO TAB HOẠT ĐỘNG!</b>\n🛒 Thêm mới thành công: <b>{total}</b> sản phẩm vào cơ sở dữ liệu.", parse_mode="HTML")
                except Exception as ex:
                    bot.send_message(message.chat.id, f"❌ <b>Lỗi cào sản phẩm từ tab:</b> <code>{str(ex)}</code>", parse_mode="HTML")
                finally:
                    db.close()
                    
            threading.Thread(target=run_crawl_active_thread, daemon=True).start()

        # Command seo <id>
        @bot.message_handler(commands=['seo'])
        def handle_seo(message):
            text = message.text.split()
            if len(text) < 2:
                bot.reply_to(message, "❌ Vui lòng nhập Product ID! Cú pháp: <code>/seo &lt;product_id&gt;</code>", parse_mode="HTML")
                return
                
            product_id = text[1]
            bot.reply_to(message, f"🤖 Đang khởi chạy tối ưu hóa SEO bằng AI cho sản phẩm ID <code>{product_id}</code>...", parse_mode="HTML")
            
            db = get_db_session()
            try:
                raw_prod = repository.get_raw_product_by_product_id(db, product_id)
                if not raw_prod:
                    bot.reply_to(message, f"❌ Không tìm thấy sản phẩm có ID: <code>{product_id}</code> trong cơ sở dữ liệu.", parse_mode="HTML")
                    return
                    
                seo_data = run_seo_generator(raw_prod.title, raw_prod.description, raw_prod.brand)
                seo_prod = repository.create_or_update_seo_product(db, product_id, seo_data)
                
                # Draw score progress bar
                score = seo_prod.seo_score or 0
                num_blocks = int(round(score / 10))
                progress_bar = "█" * num_blocks + "░" * (10 - num_blocks)
                
                # Format secondary keywords
                sec_kw_list = seo_prod.secondary_keywords or []
                if isinstance(sec_kw_list, str):
                    try:
                        import json
                        sec_kw_list = json.loads(sec_kw_list)
                    except:
                        sec_kw_list = [sec_kw_list]
                sec_kw_text = ", ".join([f"#{kw.strip()}" for kw in sec_kw_list if kw]) or "Không có"
                
                # Format USP list
                usp_list = seo_prod.usp or []
                if isinstance(usp_list, str):
                    try:
                        import json
                        usp_list = json.loads(usp_list)
                    except:
                        usp_list = [usp_list]
                usp_text = "\n".join([f"• 🌟 {item.strip()}" for item in usp_list if item]) or "• Không có"
                
                seo_response = f"""
✅ <b>TỐI ƯU HÓA SEO THÀNH CÔNG!</b>
━━━━━━━━━━━━━━━━━━━
📦 <b>Sản phẩm:</b> {raw_prod.title}
🆔 <b>Mã sản phẩm:</b> <code>{product_id}</code>

📈 <b>Điểm số SEO:</b>
<code>[{progress_bar}] {score}/100</code>

🏷️ <b>Tiêu đề SEO mới:</b>
👉 <b>{seo_prod.seo_title}</b>

🔑 <b>Từ khóa chính:</b> <code>{seo_prod.main_keyword}</code>
🏷️ <b>Từ khóa phụ:</b> <i>{sec_kw_text}</i>

🌟 <b>Lợi thế bán hàng độc nhất (USP):</b>
{usp_text}

📝 <b>Mô tả Meta (Meta Description):</b>
{seo_prod.meta_description}
━━━━━━━━━━━━━━━━━━━
💡 <i>Bước tiếp theo: Hãy gõ câu lệnh <code>/fb {product_id}</code> để soạn bài đăng quảng cáo Facebook cho sản phẩm này!</i>
                """
                bot.reply_to(message, seo_response, parse_mode="HTML")
            except Exception as e:
                bot.reply_to(message, f"❌ Lỗi khi tối ưu hóa SEO: <code>{str(e)}</code>", parse_mode="HTML")
            finally:
                db.close()

        # Command fb <id>
        @bot.message_handler(commands=['fb'])
        def handle_fb(message):
            text = message.text.split()
            if len(text) < 2:
                bot.reply_to(message, "❌ Vui lòng nhập Product ID! Cú pháp: <code>/fb &lt;product_id&gt;</code>", parse_mode="HTML")
                return
                
            product_id = text[1]
            bot.reply_to(message, f"📝 Đang khởi tạo bài đăng Facebook cho sản phẩm <code>{product_id}</code>...", parse_mode="HTML")
            
            db = get_db_session()
            try:
                raw_prod = repository.get_raw_product_by_product_id(db, product_id)
                seo_prod = repository.get_seo_product_by_product_id(db, product_id)
                if not seo_prod or not raw_prod:
                    bot.reply_to(message, f"❌ Vui lòng chạy lệnh <code>/seo {product_id}</code> cho sản phẩm trước khi tạo bài đăng Facebook!", parse_mode="HTML")
                    return
                    
                fb_data = generate_fb_content(
                    raw_prod.title, seo_prod.seo_title, seo_prod.meta_description,
                    seo_prod.main_keyword, seo_prod.secondary_keywords, seo_prod.usp
                )
                fb_post = repository.create_or_update_fb_post(db, product_id, fb_data)
                
                # Image count
                img_urls = raw_prod.images or []
                if isinstance(img_urls, str):
                    try:
                        import json
                        img_urls = json.loads(img_urls)
                    except:
                        img_urls = [img_urls] if img_urls else []
                img_count = len(img_urls)
                
                # Caption formatting
                caption = fb_post.caption or ""
                preview_length = 800
                caption_preview = caption if len(caption) <= preview_length else f"{caption[:preview_length]}...\n\n<i>[Còn tiếp...]</i>"
                
                fb_response = f"""
✅ <b>ĐÃ THÊM BÀI VIẾT VÀO HÀNG ĐỢI FACEBOOK!</b>
━━━━━━━━━━━━━━━━━━━
🆔 <b>Mã sản phẩm:</b> <code>{product_id}</code>
📊 <b>Trạng thái:</b> ⏳ <b>Pending</b> (Chờ duyệt đăng)
🖼️ <b>Hình ảnh đính kèm:</b> <b>{img_count}</b> ảnh sẵn sàng

📝 <b>Nội dung bài viết mẫu:</b>
───────────────────
{caption_preview}
───────────────────
━━━━━━━━━━━━━━━━━━━
🚀 <i>Để đăng bài viết này lên Fanpage ngay lập tức, hãy gõ câu lệnh <code>/publish</code>.</i>
                """
                bot.reply_to(message, fb_response, parse_mode="HTML")
            except Exception as e:
                bot.reply_to(message, f"❌ Lỗi khi sinh bài đăng Facebook: <code>{str(e)}</code>", parse_mode="HTML")
            finally:
                db.close()

        # Command publish
        @bot.message_handler(commands=['publish'])
        def handle_publish(message):
            bot.reply_to(message, "🚀 <b>Đang quét hàng đợi bài viết Facebook...</b>\n⚙️ <i>Đang khởi chạy trình duyệt tự động để đăng bài...</i>", parse_mode="HTML")
            
            db = get_db_session()
            try:
                posts = repository.get_all_fb_posts(db)
                pending_posts = [p for p in posts if p.status == "Pending"]
                
                if not pending_posts:
                    bot.reply_to(message, "ℹ️ Không tìm thấy bài viết nào có trạng thái <b>Pending</b> trong hàng đợi.", parse_mode="HTML")
                    return
                    
                post_to_publish = pending_posts[0]
                product_id = post_to_publish.product_id
                
                # Get raw product to get image urls
                raw_prod = repository.get_raw_product_by_product_id(db, product_id)
                image_urls = raw_prod.images if raw_prod else []
                
                # Update DB state to Publishing
                repository.update_fb_post_status(db, product_id, "Publishing")
                
                success, msg = publish_to_facebook(post_to_publish.caption, image_urls)
                if success:
                    repository.update_fb_post_status(db, product_id, "Posted")
                    bot.reply_to(message, f"🎉 <b>ĐĂNG BÀI THÀNH CÔNG!</b>\n📦 Sản phẩm ID: <code>{product_id}</code>\n📢 Kết quả: <code>{msg}</code>", parse_mode="HTML")
                else:
                    repository.update_fb_post_status(db, product_id, "Failed")
                    bot.reply_to(message, f"❌ <b>ĐĂNG BÀI THẤT BẠI!</b>\n📦 Sản phẩm ID: <code>{product_id}</code>\n⚠️ Lỗi: <code>{msg}</code>", parse_mode="HTML")
            except Exception as e:
                bot.reply_to(message, f"❌ <b>Lỗi tiến trình đăng bài:</b> <code>{str(e)}</code>", parse_mode="HTML")
            finally:
                db.close()

        # Fallback text handler for quick search & states
        @bot.message_handler(func=lambda message: True, content_types=['text'])
        def handle_text_fallback(message):
            chat_id = message.chat.id
            text = message.text.strip()
            
            # If it starts with / it's an unrecognized command
            if text.startswith('/'):
                bot.reply_to(
                    message, 
                    "❌ Câu lệnh không hợp lệ hoặc chưa được đăng ký.\n👉 Gõ /start để hiển thị menu các tùy chọn.",
                    parse_mode="HTML"
                )
                return
                
            # Check user states
            state = user_states.get(chat_id)
            
            if state == "waiting_for_search":
                user_states[chat_id] = None # Reset state
                perform_search_interactive(message, text)
                
            elif state == "waiting_for_profit_sp":
                user_states[chat_id] = None
                perform_profit_sp_interactive(chat_id, text)
                
            elif state == "waiting_for_crawl_url":
                user_states[chat_id] = None
                perform_crawl_url_interactive(chat_id, text)
                
            elif state == "waiting_for_seo_id":
                user_states[chat_id] = None
                run_seo_action_direct(chat_id, text)
                
            elif state == "waiting_for_fb_id":
                user_states[chat_id] = None
                run_fb_action_direct(chat_id, text)
                
            else:
                # If no state, treat as a quick product search
                perform_search_interactive(message, text)

        # Alert Notification Sender Helper
        def send_telegram_alert(text_msg: str):
            if chat_id:
                try:
                    bot.send_message(chat_id, text_msg)
                except Exception as ex:
                    print(f"Error sending telegram alert: {ex}")

        # Start thread
        bot_thread = threading.Thread(target=bot.infinity_polling, daemon=True)
        bot_thread.start()
        
        # Expose bot alert function
        return send_telegram_alert
    except Exception as e:
        print(f"Error starting Telegram Bot: {e}")
        return None

def send_telegram_message(text_msg: str) -> bool:
    """Send a direct telegram message using the environment token and chat ID."""
    from dotenv import load_dotenv
    load_dotenv(override=True)
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
    
    if not token or not chat_id:
        print("[Telegram Bot] Credentials not set in environment. Cannot send message.")
        return False
        
    try:
        bot = telebot.TeleBot(token)
        bot.send_message(chat_id, text_msg)
        print("[Telegram Bot] Message sent successfully.")
        return True
    except Exception as e:
        print(f"[Telegram Bot] Error sending message: {e}")
        return False

