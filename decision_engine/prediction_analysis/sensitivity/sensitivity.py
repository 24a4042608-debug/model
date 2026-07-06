from ...model_training.registry.registry import load_active_models
from ...model_training.trainer.trainer import FEATURE_COLS

def analyze_sensitivity() -> dict:
    """
    Computes sensitivity weight (feature importance) for key input variables.
    """
    models_dict, _ = load_active_models()
    if not models_dict:
        # Fallback defaults if no model exists yet
        return {
            "importance": [
                {"feature": "CVR", "weight": 0.38},
                {"feature": "CTR", "weight": 0.28},
                {"feature": "Refund", "weight": 0.20},
                {"feature": "CPA", "weight": 0.14}
            ]
        }
        
    # We aggregate feature importances across the three models (profit, gmv, roas)
    importance_map = {"ctr": 0.0, "cvr": 0.0, "cpa": 0.0, "refund": 0.0}
    
    try:
        for target, model in models_dict.items():
            if hasattr(model, "feature_importances_"):
                importances = model.feature_importances_
                for idx, col in enumerate(FEATURE_COLS):
                    # We map engineered columns back to their parent raw features
                    parent = None
                    if "ctr" in col:
                        parent = "ctr"
                    elif "cvr" in col:
                        parent = "cvr"
                    elif "cpa" in col or "cpc" in col:
                        parent = "cpa"
                    elif "refund" in col:
                        parent = "refund"
                        
                    if parent and idx < len(importances):
                        importance_map[parent] += float(importances[idx])
            elif hasattr(model, "coef_"):
                # Linear model coefficients
                coefs = np.abs(model.coef_)
                for idx, col in enumerate(FEATURE_COLS):
                    parent = None
                    if "ctr" in col:
                        parent = "ctr"
                    elif "cvr" in col:
                        parent = "cvr"
                    elif "cpa" in col or "cpc" in col:
                        parent = "cpa"
                    elif "refund" in col:
                        parent = "refund"
                        
                    if parent and idx < len(coefs):
                        importance_map[parent] += float(coefs[idx])
                        
        # Normalize weights so they sum to 1.0
        total = sum(importance_map.values())
        if total > 0:
            for k in importance_map:
                importance_map[k] = round(importance_map[k] / total, 4)
        else:
            importance_map = {"cvr": 0.38, "ctr": 0.28, "refund": 0.20, "cpa": 0.14}
            
    except Exception as e:
        print(f"Error calculating sensitivity: {e}")
        importance_map = {"cvr": 0.38, "ctr": 0.28, "refund": 0.20, "cpa": 0.14}
        
    # Convert and format labels for display
    display_names = {
        "cvr": "CVR",
        "ctr": "CTR",
        "refund": "Refund",
        "cpa": "CPA"
    }
    
    sorted_importance = []
    for k, v in importance_map.items():
        sorted_importance.append({
            "feature": display_names.get(k, k.upper()),
            "weight": v
        })
        
    sorted_importance.sort(key=lambda x: x["weight"], reverse=True)
    return {"importance": sorted_importance}
