from sqlalchemy.orm import Session
from ..optimizer.optimizer import optimize_funnel_inputs
from ...prediction_analysis.sensitivity.sensitivity import analyze_sensitivity

def generate_recommendations(db: Session, rules: dict, current_inputs: dict) -> dict:
    """
    Combines optimization results and feature sensitivity to generate prioritized action recommendations.
    """
    # 1. Run optimizer
    opt_results = optimize_funnel_inputs(db, rules, current_inputs)
    opt_inputs = opt_results["optimized_inputs"]
    opt_preds = opt_results["optimized_predictions"]
    
    # 2. Get feature sensitivity
    sensitivity = analyze_sensitivity()
    importance = {x["feature"]: x["weight"] for x in sensitivity["importance"]}
    
    # Extract current inputs
    curr_ctr = float(current_inputs.get("ctr", 2.0))
    curr_cvr = float(current_inputs.get("cvr", 4.0))
    curr_cpa = float(current_inputs.get("cpa", 25000.0))
    curr_refund = float(current_inputs.get("refund", 1.5))
    
    opt_ctr = opt_inputs["ctr"]
    opt_cvr = opt_inputs["cvr"]
    opt_cpa = opt_inputs["cpa"]
    
    actions = []
    
    # Helper to assess priorities based on optimization gap * feature importance
    cvr_diff = max(0.0, opt_cvr - curr_cvr)
    cvr_impact = cvr_diff * importance.get("CVR", 0.35)
    
    ctr_diff = max(0.0, opt_ctr - curr_ctr)
    ctr_impact = ctr_diff * importance.get("CTR", 0.25)
    
    cpa_diff = max(0.0, curr_cpa - opt_cpa)
    cpa_impact = (cpa_diff / curr_cpa) * importance.get("CPA", 0.15) if curr_cpa > 0 else 0
    
    refund_impact = 0.0
    if curr_refund > 2.0:
        refund_impact = (curr_refund - 2.0) * importance.get("Refund", 0.20)
        
    candidates = []
    
    # Action 1: CVR Optimization
    if cvr_diff > 0.1:
        candidates.append({
            "score": cvr_impact,
            "action": f"Tăng CVR lên {opt_cvr}%",
            "reason": f"Tỷ lệ chuyển đổi CVR hiện tại ({curr_cvr}%) thấp hơn mức tối ưu. CVR là chỉ số ảnh hưởng lớn nhất ({int(importance.get('CVR', 0.35)*100)}%) đến Lợi nhuận.",
            "expected_profit": f"+{round(cvr_impact * 40, 1)}%",
            "difficulty": "Medium"
        })
        
    # Action 2: CTR Optimization
    if ctr_diff > 0.1:
        candidates.append({
            "score": ctr_impact,
            "action": f"Tăng CTR lên {opt_ctr}%",
            "reason": f"Tỷ lệ nhấp chuột CTR hiện tại ({curr_ctr}%) cần nâng lên để tăng lượng khách hàng tiềm năng. Mức ảnh hưởng của CTR là {int(importance.get('CTR', 0.25)*100)}%.",
            "expected_profit": f"+{round(ctr_impact * 30, 1)}%",
            "difficulty": "Low"
        })
        
    # Action 3: CPA Bid Optimization
    if cpa_diff > 500:
        candidates.append({
            "score": cpa_impact,
            "action": f"Giảm chi phí CPA xuống dưới {int(opt_cpa):,} VNĐ",
            "reason": f"Chi phí CPA hiện tại ({int(curr_cpa):,} VNĐ) quá cao đang bào mòn chỉ số ROAS. Hãy tối ưu giá thầu và đối tượng mục tiêu quảng cáo.",
            "expected_profit": f"+{round(cpa_impact * 50, 1)}%",
            "difficulty": "Medium"
        })
        
    # Action 4: Refund Reduction
    if curr_refund > 2.0:
        candidates.append({
            "score": refund_impact,
            "action": "Giảm tỷ lệ hoàn hàng (Refund) xuống dưới 2.0%",
            "reason": f"Tỷ lệ hoàn hàng hiện tại đang cao ({curr_refund}%), trực tiếp làm hao hụt doanh thu thực tế và tăng chi phí xử lý vận hành.",
            "expected_profit": f"+{round(refund_impact * 60, 1)}%",
            "difficulty": "High"
        })
        
    # Sort by impact score descending
    candidates.sort(key=lambda x: x["score"], reverse=True)
    
    # Format list and assign priorities
    for idx, cand in enumerate(candidates):
        actions.append({
            "priority": idx + 1,
            "action": cand["action"],
            "reason": cand["reason"],
            "expected_profit": cand["expected_profit"],
            "difficulty": cand["difficulty"]
        })
        
    # Fallback default if no actions needed
    if not actions:
        actions.append({
            "priority": 1,
            "action": "Duy trì hoạt động hiện tại",
            "reason": "Các thông số hiện tại đang ở trạng thái tối ưu và đáp ứng đầy đủ mục tiêu kinh doanh.",
            "expected_profit": "0%",
            "difficulty": "Low"
        })
        
    return {
        "actions": actions,
        "rules_evaluated": rules,
        "current_predictions": opt_results["optimized_predictions"] # contains baseline estimation
    }
