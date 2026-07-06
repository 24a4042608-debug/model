def evaluate_business_rules(predictions: dict, rules: dict) -> dict:
    """
    Checks if predicted KPIs meet the designated business targets/rules.
    """
    target_profit = float(rules.get("target_profit", 5000000))
    target_roas = float(rules.get("target_roas", 4.5))
    max_refund = float(rules.get("max_refund", 3.0))
    
    pred_profit = predictions.get("profit", 0.0)
    pred_roas = predictions.get("roas", 0.0)
    pred_refund = predictions.get("refund", 0.0) # From inputs
    
    return {
        "profit_target_met": pred_profit >= target_profit,
        "roas_target_met": pred_roas >= target_roas,
        "refund_threshold_met": pred_refund <= max_refund,
        "details": {
            "profit_diff": round(pred_profit - target_profit, 2),
            "roas_diff": round(pred_roas - target_roas, 2),
            "refund_diff": round(max_refund - pred_refund, 2)
        }
    }
