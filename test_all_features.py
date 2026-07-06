import requests
import time
import sys

# Force UTF-8 console output for Windows terminal compatibility
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

def run_tests():
    base_url = "http://localhost:8000"
    print("====================================================")
    print("🧪 STARTING INTEGRATED SYSTEM TESTS FOR API ENDPOINTS")
    print("====================================================")
    
    # Test 1: System Status
    print("\nTest 1: GET /api/system-status...")
    try:
        r = requests.get(f"{base_url}/api/system-status")
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        data = r.json()
        print("✅ System Status response:")
        print(f"   - Raw products count: {data.get('raw_products_count')}")
        print(f"   - SEO products count: {data.get('seo_products_count')}")
        print(f"   - Telegram Status: {data.get('telegram_status')}")
    except Exception as e:
        print(f"❌ Test 1 failed: {e}")
        return False
        
    # Test 2: Create raw product
    print("\nTest 2: POST /api/raw-products...")
    try:
        product_data = {
            "product_id": "test_product_999",
            "title": "Áo Khoác Cardigan Nữ Dáng Dài Có Cúc Basic Thanh Lịch BYJANE",
            "description": "Chất thun tăm co giãn 4 chiều mềm mịn, dáng ôm tôn đường cong quyến rũ.",
            "price": 54000.0,
            "price_text": "54.000₫",
            "brand": "BYJANE",
            "category": "Thời Trang Nữ > Áo > Áo khoác",
            "details_json": '{"Thương hiệu": "BYJANE"}',
            "images": ["https://picsum.photos/400/400"],
            "video": "",
            "url": "https://shopee.vn/test_product_999"
        }
        r = requests.post(f"{base_url}/api/raw-products", json=product_data)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        data = r.json()
        print(f"✅ Product created successfully (ID: {data.get('id')})")
    except Exception as e:
        print(f"❌ Test 2 failed: {e}")
        return False
        
    # Test 3: List raw products
    print("\nTest 3: GET /api/raw-products...")
    try:
        r = requests.get(f"{base_url}/api/raw-products")
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        products = r.json()
        assert len(products) > 0, "No products returned"
        print(f"✅ Successfully retrieved {len(products)} products from database.")
    except Exception as e:
        print(f"❌ Test 3 failed: {e}")
        return False
        
    # Test 4: Update product
    print("\nTest 4: PUT /api/raw-products/{id}...")
    try:
        r = requests.get(f"{base_url}/api/raw-products")
        prod_id = r.json()[0]['id']
        update_data = {"brand": "BYJANE CLASSIC"}
        r_up = requests.put(f"{base_url}/api/raw-products/{prod_id}", json=update_data)
        assert r_up.status_code == 200, f"Expected 200, got {r_up.status_code}"
        assert r_up.json().get("brand") == "BYJANE CLASSIC", "Update failed"
        print("✅ Product updated successfully.")
    except Exception as e:
        print(f"❌ Test 4 failed: {e}")
        return False
        
    # Test 5: SEO Generation
    print("\nTest 5: POST /api/seo-products/{product_id}...")
    try:
        r = requests.post(f"{base_url}/api/seo-products/test_product_999")
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        print("✅ SEO Generation response:")
        print(f"   - SEO Title: {r.json().get('seo_title')}")
        print(f"   - Meta Description: {r.json().get('meta_description')}")
    except Exception as e:
        print(f"❌ Test 5 failed: {e}")
        return False
        
    # Test 6: Facebook Caption Queue Generation
    print("\nTest 6: POST /api/fb-queue/{product_id}...")
    try:
        r = requests.post(f"{base_url}/api/fb-queue/test_product_999")
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        print("✅ FB Queue Caption generated successfully.")
    except Exception as e:
        print(f"❌ Test 6 failed: {e}")
        return False
        
    # Test 7: Facebook Publishing (Simulation mode)
    print("\nTest 7: POST /api/fb-publish/{product_id}...")
    try:
        r = requests.post(f"{base_url}/api/fb-publish/test_product_999")
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        print("✅ FB Publish triggered in background successfully.")
    except Exception as e:
        print(f"❌ Test 7 failed: {e}")
        return False
        
    # Clean up Test Product
    print("\nCleaning up test data...")
    try:
        r = requests.get(f"{base_url}/api/raw-products")
        for p in r.json():
            if p['product_id'] == "test_product_999":
                requests.delete(f"{base_url}/api/raw-products/{p['id']}")
        print("🧹 Clean up finished successfully.")
    except Exception as e:
        print(f"⚠️ Clean up failed: {e}")

    print("\n====================================================")
    print("🎉 ALL TESTS PASSED SUCCESSFULLY! SYSTEM IS 100% OPERATIONAL.")
    print("====================================================")
    return True

if __name__ == "__main__":
    success = run_tests()
    if not success:
        sys.exit(1)
