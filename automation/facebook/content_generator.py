import os
import json
import time
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

def generate_fb_content(product_title: str, seo_title: str, meta_description: str, main_keyword: str, secondary_keywords: list, usps: list, api_key: str = None) -> dict:
    key = api_key or os.getenv("GEMINI_API_KEY")
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    
    if not key:
        print("No GEMINI_API_KEY configured. Running FB caption simulation...")
        time.sleep(1.0)
        
        hashtag_list = [f"#{main_keyword.replace(' ', '')}"] + [f"#{kw.replace(' ', '')}" for kw in secondary_keywords[:4]]
        hashtag_str = " ".join(hashtag_list)
        
        usp_bullet = "\n".join([f"✨ {u}" for u in usps])
        
        caption = f"""🔥 {seo_title} 🔥

Bạn đang tìm kiếm một giải pháp hoàn hảo cho phong cách thời trang năng động hàng ngày? Đừng bỏ qua siêu phẩm này nhé!

Mô tả sản phẩm:
{meta_description}

Những ưu điểm nổi bật không thể bỏ qua:
{usp_bullet}

🎯 Thích hợp mặc đi học, đi chơi, tập thể thao hay dạo phố đều cực kỳ nổi bật và thoải mái. Thiết kế trẻ trung, hiện đại nâng tầm phong cách của bạn.

🛍️ Đặt hàng ngay hôm nay để nhận ưu đãi giảm giá và miễn phí vận chuyển! Click vào giỏ hàng bên dưới nhé cả nhà!

{hashtag_str} #tiktokshop #ecommerce #muasắm"""
        
        return {
            "caption": caption,
            "hashtags": hashtag_list,
            "cta": "Mua ngay hôm nay để nhận ưu đãi cực hot!",
            "images": []
        }
        
    try:
        genai.configure(api_key=key)
        generation_config = {"response_mime_type": "application/json"}
        model = genai.GenerativeModel(model_name, generation_config=generation_config)
        
        prompt = f"""
        Bạn là chuyên gia Content Creator cho Fanpage Facebook.
        Nhiệm vụ: Viết bài viết quảng cáo sản phẩm Facebook dựa trên dữ liệu SEO:
        Tên sản phẩm gốc: {product_title}
        SEO Title: {seo_title}
        Meta Description: {meta_description}
        Từ khóa chính: {main_keyword}
        Từ khóa phụ: {", ".join(secondary_keywords)}
        USPs: {", ".join(usps)}

        Yêu cầu:
        1. Độ dài: 100 - 250 từ.
        2. Không copy y nguyên mô tả sản phẩm. Viết văn phong hấp dẫn, tự nhiên, đánh trúng tâm lý người mua.
        3. Sử dụng các dòng ngắt đoạn rõ ràng, có tiêu đề phụ thu hút.
        4. Chèn emoji hợp lý để bài viết sinh động (không nhồi nhét).
        5. Có CTA kêu gọi hành động mạnh mẽ và thu hút ở cuối.
        6. Tạo danh sách các hashtags liên quan dạng mảng chuỗi (ví dụ: ["#aosomi", "#ao_somi_nam"]).

        Trả về JSON dạng:
        {{
          "caption": "Nội dung bài viết Facebook bao gồm cả CTA và danh sách Hashtag ở cuối bài",
          "hashtags": ["#tag1", "#tag2", "#tag3"],
          "cta": "Câu kêu gọi hành động (CTA)"
        }}
        """
        
        res = model.generate_content(prompt)
        data = json.loads(res.text)
        
        return {
            "caption": data.get("caption", "").strip(),
            "hashtags": data.get("hashtags", []),
            "cta": data.get("cta", "Mua ngay hôm nay!"),
            "images": []
        }
        
    except Exception as e:
        print(f"Error in generate_fb_content: {e}")
        # Return fallback mock structure
        return {
            "caption": f"Sản phẩm mới cực chất: {seo_title}. {meta_description}. Mua ngay!",
            "hashtags": [f"#{main_keyword.replace(' ', '')}"],
            "cta": "Mua ngay!",
            "images": []
        }
