import re

def validate_title(title: str, main_keyword: str) -> tuple[bool, str]:
    title = title.strip()
    
    # 1. Length constraint: 50-60 characters
    if len(title) < 50 or len(title) > 60:
        return False, f"Title length ({len(title)} chars) must be between 50 and 60 characters."
        
    # 2. Main keyword must be at the beginning
    # Normalize comparison (lowercase, strip whitespace)
    title_lower = title.lower()
    kw_lower = main_keyword.lower().strip()
    
    if not title_lower.startswith(kw_lower):
        return False, f"Main keyword '{main_keyword}' must be at the very beginning of the title."
        
    # 3. Spam characters
    spam_patterns = [r"★+", r"!{2,}", r">{2,}", r"【", r"】"]
    for pattern in spam_patterns:
        if re.search(pattern, title):
            return False, "Title contains spam characters or excessive punctuation (e.g. ★★★, !!!, >>>)."
            
    return True, ""

def validate_description(description: str, main_keyword: str) -> tuple[bool, str]:
    description = description.strip()
    
    # 1. Length constraint: 140-160 characters
    if len(description) < 140 or len(description) > 160:
        return False, f"Description length ({len(description)} chars) must be between 140 and 160 characters."
        
    # 2. Contains main keyword
    title_lower = description.lower()
    kw_lower = main_keyword.lower().strip()
    if kw_lower not in title_lower:
        return False, f"Description must contain main keyword '{main_keyword}' naturally."
        
    # 3. Contains Call-To-Action (CTA)
    cta_words = ["mua ngay", "khám phá ngay", "đặt hàng", "khám phá", "xem ngay", "sở hữu ngay"]
    has_cta = any(cta in title_lower for cta in cta_words)
    if not has_cta:
        return False, "Description must contain a call-to-action (e.g. 'Mua ngay!', 'Khám phá ngay!')."
        
    # 4. Spam characters
    if "!!!" in description or ">>>" in description:
        return False, "Description contains spam characters (e.g. !!!, >>>)."
        
    return True, ""
