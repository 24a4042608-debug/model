from sqlalchemy.orm import Session
from datetime import datetime
from .models import RawProduct, SeoProduct, FacebookPost, Product

# ==========================================
# RAW PRODUCTS CRUD
# ==========================================

def get_raw_product_by_id(db: Session, id: int):
    return db.query(RawProduct).filter(RawProduct.id == id).first()

def get_raw_product_by_product_id(db: Session, product_id: str):
    return db.query(RawProduct).filter(RawProduct.product_id == product_id).first()

def get_all_raw_products(db: Session):
    return db.query(RawProduct).order_by(RawProduct.created_at.desc()).all()

def create_raw_product(db: Session, data: dict):
    # Check if exists
    existing = get_raw_product_by_product_id(db, data.get("product_id"))
    if existing:
        return existing
        
    db_product = RawProduct(
        product_id=data.get("product_id"),
        title=data.get("title"),
        description=data.get("description"),
        price=data.get("price"),
        price_text=data.get("price_text", ""),
        brand=data.get("brand"),
        category=data.get("category", ""),
        details_json=data.get("details_json", ""),
        images=data.get("images", []),
        video=data.get("video"),
        url=data.get("url"),
        rating_star=data.get("rating_star"),
        sold_count=data.get("sold_count")
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

def update_raw_product(db: Session, id: int, data: dict):
    db_product = get_raw_product_by_id(db, id)
    if not db_product:
        return None
        
    for key, value in data.items():
        if hasattr(db_product, key) and value is not None:
            setattr(db_product, key, value)
            
    db.commit()
    db.refresh(db_product)
    return db_product

def delete_raw_product(db: Session, id: int):
    db_product = get_raw_product_by_id(db, id)
    if not db_product:
        return False
        
    # Also delete associated SEO data and Facebook Queue post if they exist
    product_id = db_product.product_id
    seo_item = get_seo_product_by_product_id(db, product_id)
    if seo_item:
        db.delete(seo_item)
    fb_item = get_fb_post_by_product_id(db, product_id)
    if fb_item:
        db.delete(fb_item)
        
    db.delete(db_product)
    db.commit()
    return True


# ==========================================
# SEO PRODUCTS CRUD
# ==========================================

def get_seo_product_by_product_id(db: Session, product_id: str):
    return db.query(SeoProduct).filter(SeoProduct.product_id == product_id).first()

def get_all_seo_products(db: Session):
    return db.query(SeoProduct).order_by(SeoProduct.created_at.desc()).all()

def create_or_update_seo_product(db: Session, product_id: str, data: dict):
    db_seo = get_seo_product_by_product_id(db, product_id)
    
    if db_seo:
        for key, value in data.items():
            if hasattr(db_seo, key) and value is not None:
                setattr(db_seo, key, value)
    else:
        db_seo = SeoProduct(
            product_id=product_id,
            seo_title=data.get("seo_title"),
            meta_description=data.get("meta_description"),
            slug=data.get("slug"),
            main_keyword=data.get("main_keyword"),
            secondary_keywords=data.get("secondary_keywords", []),
            usp=data.get("usp", []),
            target_customer=data.get("target_customer"),
            search_intent=data.get("search_intent"),
            seo_score=data.get("seo_score", 0),
            analysis=data.get("analysis", {})
        )
        db.add(db_seo)
        
    db.commit()
    db.refresh(db_seo)
    return db_seo

def delete_seo_product(db: Session, product_id: str):
    db_seo = get_seo_product_by_product_id(db, product_id)
    if not db_seo:
        return False
    db.delete(db_seo)
    db.commit()
    return True


# ==========================================
# FACEBOOK POSTS / QUEUE CRUD
# ==========================================

def get_fb_post_by_product_id(db: Session, product_id: str):
    return db.query(FacebookPost).filter(FacebookPost.product_id == product_id).first()

def get_all_fb_posts(db: Session):
    return db.query(FacebookPost).order_by(FacebookPost.created_at.desc()).all()

def create_or_update_fb_post(db: Session, product_id: str, data: dict):
    db_post = get_fb_post_by_product_id(db, product_id)
    
    if db_post:
        for key, value in data.items():
            if hasattr(db_post, key) and value is not None:
                setattr(db_post, key, value)
    else:
        db_post = FacebookPost(
            product_id=product_id,
            caption=data.get("caption"),
            hashtags=data.get("hashtags", []),
            status=data.get("status", "Pending")
        )
        db.add(db_post)
        
    db.commit()
    db.refresh(db_post)
    return db_post

def update_fb_post_status(db: Session, product_id: str, status: str, retry: int = None):
    db_post = get_fb_post_by_product_id(db, product_id)
    if not db_post:
        return None
        
    db_post.status = status
    if retry is not None:
        db_post.retry = retry
        
    if status == "Posted":
        db_post.posted_at = datetime.utcnow()
        
    db.commit()
    db.refresh(db_post)
    return db_post

def delete_fb_post(db: Session, product_id: str):
    db_post = get_fb_post_by_product_id(db, product_id)
    if not db_post:
        return False
    db.delete(db_post)
    db.commit()
    return True

# ==========================================
# PRODUCTS CRUD
# ==========================================

def get_product_by_title_and_keyword(db: Session, title: str, keyword: str):
    return db.query(Product).filter(
        Product.title == title,
        Product.keyword == keyword
    ).first()

def create_product(db: Session, data: dict):
    # Check duplicate by title & keyword
    existing = db.query(Product).filter(
        Product.title == data.get("title"), 
        Product.keyword == data.get("keyword")
    ).first()
    if existing:
        return existing
        
    db_product = Product(
        keyword=data.get("keyword"),
        title=data.get("title"),
        price_text=data.get("price_text"),
        price_val=data.get("price_val"),
        rating_star=data.get("rating_star"),
        sold_count=data.get("sold_count"),
        image_url=data.get("image_url"),
        local_image_path=data.get("local_image_path"),
        seo_keywords=data.get("seo_keywords"),
        seo_description=data.get("seo_description"),
        product_url=data.get("product_url")
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

def clear_all_products(db: Session):
    try:
        db.query(Product).delete()
        db.query(RawProduct).delete()
        db.query(SeoProduct).delete()
        db.query(FacebookPost).delete()
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Error clearing database: {e}")
        return False

