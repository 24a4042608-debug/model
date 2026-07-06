import sys
# Adjust path to find automation package
sys.path.insert(0, "c:/Users/Admin/model")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from automation.database.models import SessionLocal, init_db, RawProduct, Product

def main():
    init_db()
    db = SessionLocal()
    raw_count = db.query(RawProduct).count()
    prod_count = db.query(Product).count()
    print(f"Database status:")
    print(f"  Raw products in DB: {raw_count}")
    print(f"  Products in DB: {prod_count}")
    
    # Print the last 5 products added
    last_products = db.query(RawProduct).order_by(RawProduct.id.desc()).limit(5).all()
    if last_products:
        print("\nLast 5 products:")
        for p in last_products:
            print(f"  - ID: {p.product_id}")
            print(f"    Title: {p.title[:50]}...")
            print(f"    Price: {p.price_text} ({p.price})")
            print(f"    Rating: {p.rating_star}")
            print(f"    Sold Count: {p.sold_count}")
    db.close()

if __name__ == "__main__":
    main()
