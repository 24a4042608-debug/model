import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from automation.database.models import TrainingDataset
from ...dataset_management.feature_engineering.feature_engineering import calculate_engineered_features, add_temporal_features
from ..evaluator.evaluator import evaluate_predictions
from ..registry.registry import register_model

FEATURE_COLS = [
    "ctr", "cvr", "cpc", "cpa", "refund",
    "profit_margin", "aov", "weekday", "review_score",
    "inventory_days", "discount_pct", "campaign_type",
    "ctr_trend", "ctr_growth", "cvr_trend", "cvr_growth",
    "roas_trend", "roas_growth", "refund_trend", "refund_growth",
    "hour_of_day", "time_block", "is_holiday", "days_to_flash_sale",
    "day_of_month", "is_salary_period", "month"
]

TARGET_COLS = ["profit", "gmv", "roas"]

def seed_default_training_data(db: Session):
    """
    Seeds realistic mock training records if database is empty.
    """
    print("[Trainer] Database is empty. Seeding mock training records...")
    
    # Let's generate daily performance for 2 products for 60 days
    products = [
        {"id": "prod_byjane315", "base_ctr": 2.5, "base_cvr": 5.0, "base_cpc": 1200, "base_cpa": 24000, "base_refund": 1.2, "base_price": 185000},
        {"id": "prod_ultralight", "base_ctr": 1.8, "base_cvr": 3.5, "base_cpc": 2000, "base_cpa": 57000, "base_refund": 2.5, "base_price": 480000}
    ]
    
    today = datetime.now()
    records_to_add = []
    
    for day_offset in range(60, 0, -1):
        record_date = (today - timedelta(days=day_offset)).strftime("%Y-%m-%d")
        
        for p in products:
            # Add some random variations to make it realistic
            ctr = max(0.5, p["base_ctr"] + np.random.normal(0, 0.4))
            cvr = max(0.5, p["base_cvr"] + np.random.normal(0, 0.6))
            cpc = max(500, p["base_cpc"] + int(np.random.normal(0, 150)))
            cpa = max(10000, p["base_cpa"] + int(np.random.normal(0, 2000)))
            refund = max(0.0, p["base_refund"] + np.random.normal(0, 0.5))
            
            # Estimate traffic and sales
            clicks = int(np.random.randint(500, 2000))
            conversions = int(clicks * (cvr / 100))
            if conversions == 0:
                conversions = 1
                
            gmv = conversions * p["base_price"]
            cost = conversions * cpa
            profit = gmv * 0.35 - cost - (gmv * (refund / 100)) # Profit estimation
            roas = gmv / cost if cost > 0 else 1.0
            
            records_to_add.append(TrainingDataset(
                product_id=p["id"],
                date=record_date,
                ctr=round(ctr, 2),
                cvr=round(cvr, 2),
                cpc=round(cpc, 2),
                cpa=round(cpa, 2),
                roas=round(roas, 2),
                refund=round(refund, 2),
                gmv=round(gmv, 2),
                profit=round(profit, 2)
            ))
            
    db.add_all(records_to_add)
    db.commit()
    print(f"[Trainer] Seeded {len(records_to_add)} records successfully.")

def train_decision_model(db: Session, algorithm: str = "XGBoost") -> dict:
    """
    Trains models for profit, gmv, and roas using the specified algorithm.
    """
    # 1. Check database counts
    count = db.query(TrainingDataset).count()
    if count < 10:
        seed_default_training_data(db)
        
    records = db.query(TrainingDataset).all()
    
    # 2. Extract and Feature Engineer
    raw_data = []
    for r in records:
        raw_data.append({
            "product_id": r.product_id,
            "date": r.date,
            "ctr": float(r.ctr),
            "cvr": float(r.cvr),
            "cpc": float(r.cpc),
            "cpa": float(r.cpa),
            "roas": float(r.roas),
            "refund": float(r.refund),
            "gmv": float(r.gmv),
            "profit": float(r.profit)
        })
        
    # Convert to list of feature engineered records
    processed_records = []
    for r in raw_data:
        engineered = calculate_engineered_features(r, db)
        full_row = r.copy()
        full_row.update(engineered)
        processed_records.append(full_row)
        
    df = pd.DataFrame(processed_records)
    
    # ── ĐIỂM 1: Thêm biến thời gian ────────────────────────
    df = add_temporal_features(df)
    
    # 3. Prepare datasets
    X = df[FEATURE_COLS].values
    y = df[TARGET_COLS].values
    
    # Train-test split (80/20)
    split_idx = int(len(df) * 0.8)
    indices = np.random.permutation(len(df))
    train_idx, test_idx = indices[:split_idx], indices[split_idx:]
    
    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]
    
    # 4. Choose algorithm
    models = {}
    r2_scores = []
    
    for i, target in enumerate(TARGET_COLS):
        y_train_target = y_train[:, i]
        y_test_target = y_test[:, i]
        
        # Instantiate model based on algorithm selection
        if algorithm == "XGBoost":
            import xgboost as xgb
            model = xgb.XGBRegressor(n_estimators=100, max_depth=5, learning_rate=0.1, random_state=42)
        elif algorithm == "LightGBM":
            import lightgbm as lgb
            model = lgb.LGBMRegressor(n_estimators=100, max_depth=5, learning_rate=0.1, random_state=42, verbose=-1)
        elif algorithm == "CatBoost":
            try:
                import catboost as cb
                model = cb.CatBoostRegressor(iterations=100, depth=5, learning_rate=0.1, random_seed=42, verbose=0)
            except ImportError:
                print("[Trainer] CatBoost not installed. Falling back to XGBoost...")
                import xgboost as xgb
                model = xgb.XGBRegressor(n_estimators=100, max_depth=5, learning_rate=0.1, random_state=42)
                algorithm = "XGBoost" # Update algorithm metadata
        elif algorithm == "RandomForest":
            from sklearn.ensemble import RandomForestRegressor
            model = RandomForestRegressor(n_estimators=100, max_depth=6, random_state=42)
        else: # Linear Regression fallback
            from sklearn.linear_model import Ridge
            model = Ridge()
            
        model.fit(X_train, y_train_target)
        
        # Evaluate
        preds = model.predict(X_test)
        metrics = evaluate_predictions(y_test_target, preds)
        r2_scores.append(metrics["r2_score"])
        
        models[target] = model
        
    # ── ĐIỂM 2: Tính 4 factors từ data thực tế ─────────────
    from .dynamic_factors import compute_alpha, compute_beta, compute_gamma, compute_delta, adjust_predictions
    
    alpha = compute_alpha(df.tail(7), df)
    beta  = compute_beta()           # tự lấy date.today()
    gamma = compute_gamma(
        roas_trend=df["roas_trend"].mean() if "roas_trend" in df.columns else 0.0,
        ctr_growth=df["ctr_growth"].mean() if "ctr_growth" in df.columns else 0.0
    )
    delta = compute_delta(
        refund_trend=df["refund_trend"].mean() if "refund_trend" in df.columns else 0.0,
        inventory_days=df["inventory_days"].mean() if "inventory_days" in df.columns else 15.0
    )
    
    # ── ĐIỂM 3: Hiệu chỉnh từng dự đoán ────────────────────
    # TARGET_COLS = ["profit", "gmv", "roas"]
    raw_profit = models["profit"].predict(X_test)
    raw_gmv = models["gmv"].predict(X_test)
    raw_roas = models["roas"].predict(X_test)
    
    adjusted_results = []
    for r_r, g_r, p_r in zip(raw_roas, raw_gmv, raw_profit):
        result = adjust_predictions(r_r, g_r, p_r, alpha, beta, gamma, delta)
        adjusted_results.append(result)
        
    print(f"[Trainer] Adjusted test results size: {len(adjusted_results)}")
    
    avg_accuracy = max(0.0, min(1.0, np.mean(r2_scores)))
    
    # 5. Register models
    metadata = register_model(
        models_dict=models,
        algorithm=algorithm,
        accuracy=avg_accuracy,
        dataset_size=len(df)
    )
    
    return metadata

def run_test_train():
    from automation.database.models import SessionLocal
    db = SessionLocal()
    try:
        meta = train_decision_model(db, "XGBoost")
        print("Training successful! Metadata:", meta)
    finally:
        db.close()
