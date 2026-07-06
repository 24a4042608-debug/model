import sys
# Adjust path to find automation package
sys.path.insert(0, "c:/Users/Admin/model")

from automation.database.models import SessionLocal, init_db, RawProduct, Product, SeoProduct, FacebookPost
from automation.crawler.shopee_crawler import crawl_active_shopee_tab

def main():
    init_db()
    db = SessionLocal()
    
    print("🧹 Clearing all products from database...")
    db.query(FacebookPost).delete()
    db.query(SeoProduct).delete()
    db.query(Product).delete()
    db.query(RawProduct).delete()
    db.commit()
    print("✅ Database cleared successfully!")
    
    print("\n🚀 Starting active Shopee tab crawl with updated parser and scrolling...")
    try:
        total = crawl_active_shopee_tab(db)
        print(f"\n🏁 Completed! Added {total} products with full details (Rating, Sold, Price, Description)!")
    except Exception as e:
        print(f"❌ Error during crawl: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
