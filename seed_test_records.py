import os
import sys
import random
from datetime import datetime, timedelta

# Add current directory to path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from automation.database.models import SessionLocal, TrainingDataset

PRODUCTS = [
    {"id": "ao_thun_local_brand_unisex", "price": 185000, "refund_rate": 2.5},
    {"id": "son_kem_li_matte_blackrouge", "price": 160000, "refund_rate": 1.2},
    {"id": "kem_chong_nang_la_roche_posay", "price": 380000, "refund_rate": 0.8},
    {"id": "vay_hoa_nhi_vintage_dang_xoe", "price": 270000, "refund_rate": 4.0}
]

def seed_data():
    db = SessionLocal()
    try:
        print("Clearing old records from TrainingDataset table...")
        db.query(TrainingDataset).delete()
        db.commit()
        
        print("Generating 100 realistic social media campaign records...")
        today = datetime.now()
        records = []
        
        for i in range(100, 0, -1):
            dt = today - timedelta(days=i)
            record_date = dt.strftime("%Y-%m-%d")
            
            # Select a random product for this campaign day
            prod = random.choice(PRODUCTS)
            product_id = prod["id"]
            price = prod["price"]
            refund_rate = prod["refund_rate"]
            
            # Determine seasonality modifiers
            is_weekend = dt.weekday() in [4, 5, 6] # Fri, Sat, Sun
            is_double_day = dt.day in [1, 2, 5, 6, 7, 8, 9, 10, 11, 12, 15, 25] # Special sale events
            
            # Base daily ad spending budget (in VND)
            base_budget = random.randint(250000, 1200000)
            if is_double_day:
                base_budget *= random.uniform(1.8, 3.2)
            elif is_weekend:
                base_budget *= random.uniform(1.1, 1.4)
                
            budget = int(base_budget)
            
            # CPC (Cost per Click) in VND
            base_cpc = random.randint(450, 950)
            # Weekend/Sale competition spikes CPC slightly
            if is_double_day:
                base_cpc *= random.uniform(1.1, 1.3)
            cpc = round(base_cpc, 2)
            
            # Click count
            clicks = int(budget / cpc)
            if clicks == 0:
                clicks = 1
                
            # CTR (Click Through Rate)
            base_ctr = random.uniform(1.8, 3.8)
            if is_double_day:
                base_ctr += random.uniform(0.5, 1.2)
            elif is_weekend:
                base_ctr += random.uniform(0.2, 0.5)
            ctr = round(base_ctr, 2)
            
            # Impressions derived from CTR and Clicks
            impressions = int(clicks / (ctr / 100))
            
            # CVR (Conversion Rate)
            base_cvr = random.uniform(2.2, 4.8)
            if is_double_day:
                base_cvr += random.uniform(1.0, 2.5)
            elif is_weekend:
                base_cvr += random.uniform(0.3, 0.8)
            cvr = round(base_cvr, 2)
            
            # Conversions
            conversions = int(clicks * (cvr / 100))
            if conversions == 0:
                conversions = random.randint(1, 3)
                
            # Derived Cost and Revenue
            cost = clicks * cpc
            gmv = conversions * price
            
            # CPA (Cost per Acquisition)
            cpa = round(cost / conversions, 2)
            
            # ROAS (Return on Ad Spend)
            roas = round(gmv / cost, 2)
            
            # Refund Rate
            refund = round(refund_rate + random.uniform(-0.5, 0.5), 2)
            refund = max(0.1, refund)
            
            # Net profit (45% average product margin before ad costs and refund writeoffs)
            profit = round(gmv * 0.45 - cost - (gmv * (refund / 100)), 2)
            
            records.append(TrainingDataset(
                product_id=product_id,
                date=record_date,
                ctr=ctr,
                cvr=cvr,
                cpc=cpc,
                cpa=int(cpa),
                roas=roas,
                refund=refund,
                gmv=gmv,
                profit=profit
            ))
            
        db.add_all(records)
        db.commit()
        print(f"Success: Seeded {len(records)} realistic campaign records in database.")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
