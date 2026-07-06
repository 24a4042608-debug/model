from sqlalchemy.orm import Session
from ..predictor.predictor import predict_kpis

def run_whatif_simulation(db: Session, baseline: dict, modified: dict) -> dict:
    """
    Simulates KPI changes between a baseline configuration and a modified/what-if configuration.
    """
    base_preds = predict_kpis(db, baseline)
    mod_preds = predict_kpis(db, modified)
    
    simulation_results = {
        "baseline": base_preds,
        "modified": mod_preds,
        "changes_percent": {}
    }
    
    for kpi in ["profit", "gmv", "roas"]:
        b_val = base_preds[kpi]
        m_val = mod_preds[kpi]
        
        if b_val != 0:
            pct_change = ((m_val - b_val) / abs(b_val)) * 100
        else:
            pct_change = 0.0
            
        simulation_results["changes_percent"][kpi] = round(pct_change, 2)
        
    return simulation_results
