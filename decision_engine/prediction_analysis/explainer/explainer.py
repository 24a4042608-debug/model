def explain_simulation_impact(simulation_data: dict, sensitivity_data: dict) -> dict:
    """
    Generates dynamic Vietnamese explanations for the what-if simulation results.
    """
    baseline_in = simulation_data.get("baseline", {})
    changes = simulation_data.get("changes_percent", {})
    importance_list = sensitivity_data.get("importance", [])
    
    # Identify top key features
    top_feature = importance_list[0]["feature"] if importance_list else "CVR"
    
    explanation_lines = []
    
    profit_change = changes.get("profit", 0.0)
    gmv_change = changes.get("gmv", 0.0)
    roas_change = changes.get("roas", 0.0)
    
    # 1. Headline summary
    if profit_change > 0:
        headline = f"📈 Dự báo Lợi nhuận tăng thêm **{profit_change}%** và GMV tăng **{gmv_change}%**."
    elif profit_change < 0:
        headline = f"📉 Tổ hợp này có thể làm giảm Lợi nhuận xuống **{abs(profit_change)}%**."
    else:
        headline = "⚖️ Không có sự thay đổi đáng kể về Lợi nhuận và Doanh thu."
        
    explanation_lines.append(headline)
    
    # 2. Sensitivity mapping
    explanation_lines.append(
        f"Mô hình ML xác định **{top_feature}** là yếu tố có sức ảnh hưởng mạnh nhất đến kết quả tài chính của bạn."
    )
    
    # 3. Specific explanations
    if roas_change > 0:
        explanation_lines.append(
            f"Chỉ số ROAS của bạn tăng **{roas_change}%** do chi phí quảng cáo (CPA) được tối ưu hiệu quả hơn so với doanh số mang lại."
        )
    elif roas_change < 0:
        explanation_lines.append(
            f"Cảnh báo: ROAS giảm **{abs(roas_change)}%**, hãy cẩn trọng vì chi phí CPA có thể đang tăng quá mức so với tốc độ tăng trưởng GMV."
        )
        
    # Combine explanation
    full_text = " ".join(explanation_lines)
    
    return {
        "explanation": full_text,
        "summary_metrics": {
            "profit_growth": f"{'+' if profit_change > 0 else ''}{profit_change}%",
            "gmv_growth": f"{'+' if gmv_change > 0 else ''}{gmv_change}%",
            "roas_growth": f"{'+' if roas_change > 0 else ''}{roas_change}%"
        }
    }
