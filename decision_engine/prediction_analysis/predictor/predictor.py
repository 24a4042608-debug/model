import numpy as np
import pandas as pd
from datetime import datetime
from sqlalchemy.orm import Session
from ...model_training.registry.registry import load_active_models
from ...model_training.trainer.trainer import train_decision_model, FEATURE_COLS
from ...dataset_management.feature_engineering.feature_engineering import calculate_engineered_features
from ...model_training.trainer.dynamic_factors import compute_alpha, compute_beta, compute_gamma, compute_delta, adjust_predictions
from automation.database.models import TrainingDataset

def predict_kpis(db: Session, inputs: dict) -> dict:
    """
    Predicts GMV, Profit, and ROAS based on inputs (ctr, cvr, cpa, refund).
    Imputes engineered features for prediction.
    """
    # 1. Load models
    models_dict, metadata = load_active_models()
    if not models_dict:
        # If no active model, train one now automatically using default XGBoost
        print("[Predictor] No active model found. Auto-training now...")
        metadata = train_decision_model(db, "XGBoost")
        models_dict, metadata = load_active_models()
        if not models_dict:
            raise Exception("Failed to load or train predictive models.")
            
    # 2. Impute inputs
    ctr = float(inputs.get("ctr", 2.0))
    cvr = float(inputs.get("cvr", 4.0))
    cpa = float(inputs.get("cpa", 25000.0))
    refund = float(inputs.get("refund", 1.5))
    
    # Mathematical relations
    cpc = cpa * (cvr / 100.0)
    aov = 250000.0 # Standard AOV fallback
    profit_margin = 0.35 - (refund / 100.0) - (cpa / aov if aov > 0 else 0)
    
    weekday = float(datetime.now().weekday())
    review_score = max(1.0, min(5.0, 5.0 - (refund / 10.0)))
    inventory_days = 15.0
    discount_pct = 10.0
    campaign_type = 2.0 # Regular
    
    date_str = inputs.get("date") or datetime.now().strftime("%Y-%m-%d")
    
    # ── ĐIỂM 1: Thêm biến thời gian ────────────────────────
    FLASH_SALE_DATES = ["2025-10-10", "2025-11-11", "2025-12-12", "2026-03-08"]
    HOLIDAY_DATES    = ["2025-01-01", "2025-04-30", "2025-05-01", "2025-09-02"]
    
    try:
        dt = datetime.strptime(date_str[:10], "%Y-%m-%d")
    except Exception:
        dt = datetime.now()
        
    month = float(dt.month)
    day_of_month = float(dt.day)
    hour_of_day = float(inputs.get("hour_of_day", 12.0))
    time_block = float(hour_of_day // 6)
    
    today_str = dt.strftime("%Y-%m-%d")
    is_holiday = 1.0 if today_str in HOLIDAY_DATES else 0.0
    is_salary_period = 1.0 if (day_of_month >= 25 or day_of_month <= 5) else 0.0
    
    flash_dates = [datetime.strptime(d, "%Y-%m-%d") for d in FLASH_SALE_DATES]
    min_days = 999
    for fd in flash_dates:
        diff = (fd - dt).days
        if 0 <= diff < min_days:
            min_days = diff
    days_to_flash_sale = float(min_days)
    
    # Historical values fallback to 0.0 for simulation inputs
    feature_row = {
        "ctr": ctr, "cvr": cvr, "cpc": cpc, "cpa": cpa, "refund": refund,
        "profit_margin": profit_margin, "aov": aov, "weekday": weekday,
        "review_score": review_score, "inventory_days": inventory_days,
        "discount_pct": discount_pct, "campaign_type": campaign_type,
        "ctr_trend": 0.0, "ctr_growth": 0.0,
        "cvr_trend": 0.0, "cvr_growth": 0.0,
        "roas_trend": 0.0, "roas_growth": 0.0,
        "refund_trend": 0.0, "refund_growth": 0.0,
        "month": month,
        "day_of_month": day_of_month,
        "hour_of_day": hour_of_day,
        "time_block": time_block,
        "is_holiday": is_holiday,
        "is_salary_period": is_salary_period,
        "days_to_flash_sale": days_to_flash_sale
    }
    
    # 3. Create DataFrame matching training columns
    df_row = pd.DataFrame([feature_row])
    X = df_row[FEATURE_COLS].values
    
    # 4. Predict
    raw_preds = {}
    for target, model in models_dict.items():
        pred_val = model.predict(X)[0]
        # Keep physical boundaries (ROAS, GMV >= 0)
        if target in ["gmv", "roas"]:
            pred_val = max(0.0, float(pred_val))
        raw_preds[target] = float(pred_val)
        
    # ── ĐIỂM 2: Tính 4 factors từ data thực tế ─────────────
    records = db.query(TrainingDataset).order_by(TrainingDataset.date.asc()).all() if db else []
    
    df_all = None
    df_recent = None
    roas_trend = 0.0
    ctr_growth = 0.0
    refund_trend = 0.0
    inventory_days_val = 15.0
    
    if len(records) >= 2:
        df_all = pd.DataFrame([{
            "date": r.date,
            "roas": float(r.roas)
        } for r in records])
        df_recent = df_all.tail(7)
        
        processed_records = []
        for r in records:
            engineered = calculate_engineered_features({
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
            }, db)
            processed_records.append(engineered)
            
        df_features = pd.DataFrame(processed_records)
        if len(df_features) > 0:
            roas_trend = df_features["roas_trend"].mean()
            ctr_growth = df_features["ctr_growth"].mean()
            refund_trend = df_features["refund_trend"].mean()
            inventory_days_val = df_features["inventory_days"].mean()
            
    alpha = compute_alpha(df_recent, df_all)
    beta = compute_beta()
    gamma = compute_gamma(roas_trend, ctr_growth)
    delta = compute_delta(refund_trend, inventory_days_val)
    
    # ── ĐIỂM 3: Hiệu chỉnh từng dự đoán ────────────────────
    adjusted = adjust_predictions(
        raw_preds.get("roas", 1.0),
        raw_preds.get("gmv", 0.0),
        raw_preds.get("profit", 0.0),
        alpha, beta, gamma, delta
    )
    
    results = {
        "roas": adjusted["roas_adj"],
        "gmv": adjusted["gmv_adj"],
        "profit": adjusted["profit_adj"],
        "factors": adjusted["factors"],
        "confidence": int(metadata.get("accuracy", 0.90) * 100)
    }
    return results

