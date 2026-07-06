import numpy as np
from scipy.optimize import minimize
from sqlalchemy.orm import Session
from ...prediction_analysis.predictor.predictor import predict_kpis

def optimize_funnel_inputs(db: Session, rules: dict, current_inputs: dict) -> dict:
    """
    Optimizes CTR, CVR, and CPA to maximize Profit while satisfying business constraints.
    Uses Scipy Nelder-Mead direct optimization.
    """
    target_roas = float(rules.get("target_roas", 4.5))
    target_profit = float(rules.get("target_profit", 5000000))
    refund = float(current_inputs.get("refund", 1.5))
    
    # Bounds for inputs
    bounds = {
        "ctr": (0.5, 6.0),    # 0.5% to 6%
        "cvr": (0.5, 12.0),   # 0.5% to 12%
        "cpa": (5000.0, 150000.0) # 5k to 150k VND
    }
    
    # Initial guess
    x0 = [
        float(current_inputs.get("ctr", 2.0)),
        float(current_inputs.get("cvr", 4.0)),
        float(current_inputs.get("cpa", 25000.0))
    ]
    
    def objective(x):
        ctr, cvr, cpa = x
        
        # Enforce bounds via extreme penalties
        if not (bounds["ctr"][0] <= ctr <= bounds["ctr"][1]):
            return 1e15
        if not (bounds["cvr"][0] <= cvr <= bounds["cvr"][1]):
            return 1e15
        if not (bounds["cpa"][0] <= cpa <= bounds["cpa"][1]):
            return 1e15
            
        preds = predict_kpis(db, {"ctr": ctr, "cvr": cvr, "cpa": cpa, "refund": refund})
        profit = preds["profit"]
        roas = preds["roas"]
        
        # We minimize negative profit (to maximize profit)
        score = -profit
        
        # Add penalty for failing ROAS target
        if roas < target_roas:
            score += (target_roas - roas) * 5000000 # Penalty scale
            
        return score

    # Optimize using Nelder-Mead
    res = minimize(objective, x0, method="Nelder-Mead", options={"maxiter": 100})
    
    # Get optimal outputs
    opt_ctr, opt_cvr, opt_cpa = res.x
    
    # Clip back to boundaries just in case
    opt_ctr = max(bounds["ctr"][0], min(bounds["ctr"][1], opt_ctr))
    opt_cvr = max(bounds["cvr"][0], min(bounds["cvr"][1], opt_cvr))
    opt_cpa = max(bounds["cpa"][0], min(bounds["cpa"][1], opt_cpa))
    
    optimized_inputs = {
        "ctr": round(float(opt_ctr), 2),
        "cvr": round(float(opt_cvr), 2),
        "cpa": round(float(opt_cpa), 0),
        "refund": refund
    }
    
    optimized_predictions = predict_kpis(db, optimized_inputs)
    
    return {
        "optimized_inputs": optimized_inputs,
        "optimized_predictions": optimized_predictions,
        "success": bool(res.success)
    }
