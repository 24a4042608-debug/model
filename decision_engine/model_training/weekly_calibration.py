# weekly_calibration.py (chạy mỗi thứ Hai lúc 2:00 AM qua cron)
import pandas as pd
import numpy as np
from datetime import datetime
from .trainer.dynamic_factors import load_weights, save_weights, SEASONAL_BETA_TABLE

def calibrate(df_actual: pd.DataFrame, df_predicted: pd.DataFrame):
    """
    df_actual: cột roas_actual, gmv_actual, profit_actual
    df_predicted: cột roas_adj, gmv_adj, profit_adj, alpha, beta, gamma, delta
    """
    # Merge
    on_cols = []
    if "record_id" in df_actual.columns and "record_id" in df_predicted.columns:
        on_cols = ["record_id"]
    elif "id" in df_actual.columns and "id" in df_predicted.columns:
        on_cols = ["id"]
    else:
        on_cols = ["product_id", "date"]
        
    merged = df_actual.merge(df_predicted, on=on_cols)
    if len(merged) == 0:
        print("[Calibration] No records matched. Calibration skipped.")
        return
        
    # Tính error theo từng factor group
    merged["error_log"] = np.log(merged["roas_actual"] / np.clip(merged["roas_adj"], 0.01, None))
    
    w = load_weights()
    lr = 0.05 # learning rate
    
    # Gradient descent đơn giản trên log-loss
    for key, col in [("w1", "alpha"), ("w2", "beta"), ("w3", "gamma"), ("w4", "delta")]:
        factor_deviation = merged[col] - 1.0 if col != "delta" else 1.0 - merged[col]
        grad = -2.0 * (merged["error_log"] * factor_deviation).mean()
        w[key] = float(np.clip(w[key] - lr * grad, 0.05, 0.8))
        
    save_weights(w)
    
    # Cập nhật bảng beta theo tháng từ thực tế
    if "date" in merged.columns:
        merged["timestamp"] = pd.to_datetime(merged["date"])
    elif "timestamp" not in merged.columns:
        merged["timestamp"] = pd.to_datetime(datetime.now())
        
    for month in range(1, 13):
        subset = merged[merged["timestamp"].dt.month == month]
        if len(subset) >= 30:
            actual_ratio = (subset["roas_actual"] / subset["roas_adj"]).median()
            SEASONAL_BETA_TABLE[month] = round(
                SEASONAL_BETA_TABLE[month] * (0.8 + 0.2 * actual_ratio), 3
            )
            
    print(f"Calibration done. New weights: {w}")
    print(f"Updated beta table: {SEASONAL_BETA_TABLE}")
