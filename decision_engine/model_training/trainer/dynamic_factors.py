import numpy as np
import json
import os
from datetime import datetime, date
from typing import Optional

FLASH_SALE_DATES = ["2025-10-10", "2025-11-11", "2025-12-12", "2026-03-08"]
HOLIDAY_DATES    = ["2025-01-01", "2025-04-30", "2025-05-01", "2025-09-02"]

# Bảng beta theo tháng - cập nhật mỗi quý từ kết quả thực tế
SEASONAL_BETA_TABLE = {
    1: 1.35, # Tết
    2: 0.85,
    3: 0.90,
    4: 0.95,
    5: 0.80,
    6: 0.75,
    7: 0.72,
    8: 0.78,
    9: 0.88,
    10: 1.20, # 10/10
    11: 1.55, # 11/11
    12: 1.30  # 12/12
}

# Trọng số w1-w4 - được weekly calibration job cập nhật
WEIGHTS_PATH = "models/factor_weights.json"
DEFAULT_WEIGHTS = {"w1": 0.3, "w2": 0.4, "w3": 0.2, "w4": 0.1}

def load_weights(db=None) -> dict:
    if db:
        try:
            from automation.database.models import SystemSetting
            setting = db.query(SystemSetting).filter(SystemSetting.key == "factor_weights").first()
            if setting:
                return setting.value
        except Exception as e:
            print(f"Error loading weights from DB: {e}")
            
    if os.path.exists(WEIGHTS_PATH):
        try:
            with open(WEIGHTS_PATH, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return DEFAULT_WEIGHTS

def save_weights(weights: dict, db=None):
    if db:
        try:
            from automation.database.models import SystemSetting
            setting = db.query(SystemSetting).filter(SystemSetting.key == "factor_weights").first()
            if not setting:
                setting = SystemSetting(key="factor_weights", value=weights)
                db.add(setting)
            else:
                setting.value = weights
            db.commit()
            return
        except Exception as e:
            print(f"Error saving weights to DB: {e}")
            
    os.makedirs("models", exist_ok=True)
    with open(WEIGHTS_PATH, "w") as f:
        json.dump(weights, f, indent=2)

def compute_alpha(df_recent, df_all) -> float:
    """Tin cậy data mới: so sánh variance 7 ngày gần nhất vs toàn bộ."""
    if df_recent is None or len(df_recent) < 2 or df_all is None or len(df_all) < 2:
        return 1.0
    recent_std = df_recent["roas"].std()
    all_std = df_all["roas"].std()
    if all_std == 0 or np.isnan(all_std) or np.isnan(recent_std):
        return 1.0
    # Tỷ lệ biến động
    ratio = recent_std / all_std
    # alpha gần 1 nếu ratio gần 1. Nếu biến động mạnh thì alpha giảm xuống (ít tin cậy data mới)
    alpha = 1.0 / (1.0 + np.clip(ratio - 1.0, 0, 0.5))
    return float(alpha)

def compute_beta() -> float:
    """Hệ số mùa vụ (beta) dựa trên khoảng cách tới sự kiện, tháng và ngày lễ."""
    today_val = date.today()
    month_val = today_val.month
    base_beta = SEASONAL_BETA_TABLE.get(month_val, 1.0)
    
    # Check holiday
    today_str = today_val.strftime("%Y-%m-%d")
    if today_str in HOLIDAY_DATES:
        return float(base_beta * 1.2)
        
    # Check flash sale
    min_days = 999
    for d_str in FLASH_SALE_DATES:
        try:
            d_val = datetime.strptime(d_str, "%Y-%m-%d").date()
            diff = (d_val - today_val).days
            if 0 <= diff < min_days:
                min_days = diff
        except Exception:
            pass
            
    if min_days <= 3:
        # Flash sale multiplier
        boost = 1.3 - (min_days * 0.08)
        return float(base_beta * boost)
    return float(base_beta)

def compute_gamma(roas_trend: float, ctr_growth: float) -> float:
    gamma = 1.0 + 0.5 * roas_trend + 0.3 * ctr_growth
    return float(np.clip(gamma, 0.7, 1.5))

def compute_delta(refund_trend: float, inventory_days: float) -> float:
    """Hệ số rủi ro: cao -> ít rủi ro, thấp -> nhiều rủi ro."""
    risk_score = 0.5 * max(refund_trend, 0) + 0.5 * max((inventory_days - 30) / 60, 0)
    delta = 1.0 - np.clip(risk_score, 0, 0.4)
    return float(delta)

def adjust_predictions(roas_raw: float, gmv_raw: float, profit_raw: float,
                      alpha: float, beta: float, gamma: float, delta: float,
                      weights: Optional[dict] = None) -> dict:
    """
    Hiệu chỉnh dự đoán theo log-space để tránh nhân lũy mất kiểm soát.
    ROAS_adj = exp(log(ROAS_raw) + w1*(a-1) + w2*(b-1) + w3*(g-1) + w4*(1-d))
    """
    w = weights or load_weights()
    correction = (
        w.get("w1", 0.3) * (alpha - 1.0) +
        w.get("w2", 0.4) * (beta - 1.0) +
        w.get("w3", 0.2) * (gamma - 1.0) +
        w.get("w4", 0.1) * (1.0 - delta)
    )
    roas_adj    = float(np.exp(np.log(max(roas_raw,   0.01)) + correction))
    gmv_adj     = float(np.exp(np.log(max(gmv_raw,    0.01)) + correction))
    profit_adj  = float(np.exp(np.log(max(profit_raw + 1e6, 1.0)) + correction) - 1e6)
    return {
        "roas_adj":     round(roas_adj,     4),
        "gmv_adj":      round(gmv_adj,      2),
        "profit_adj":   round(profit_adj,   2),
        "factors": {
            "alpha":    round(alpha,    4),
            "beta":     round(beta,     4),
            "gamma":    round(gamma,    4),
            "delta":    round(delta,    4),
        },
        "correction_log": round(correction, 4),
    }
