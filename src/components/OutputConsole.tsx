import React, { useState } from "react";
import { Copy, Check, FileJson, BarChart3, AlertCircle } from "lucide-react";
import type { SEOResult } from "../services/seoPipeline";

interface OutputConsoleProps {
  result: SEOResult | null;
}

export const OutputConsole: React.FC<OutputConsoleProps> = ({ result }) => {
  const [activeTab, setActiveTab] = useState<"analysis" | "json">("analysis");
  const [copied, setCopied] = useState(false);

  if (!result) {
    return (
      <div className="output-console-empty">
        <BarChart3 size={48} className="empty-icon" />
        <h3>Kết quả SEO sẽ hiển thị ở đây</h3>
        <p>Nhập thông tin sản phẩm ở bảng điều khiển bên trái và nhấn "Tối ưu hóa SEO" để bắt đầu.</p>
      </div>
    );
  }

  const handleCopy = () => {
    // Generate the exact output format requested by the user
    const exportJson = {
      seo_title: result.seo_title,
      meta_description: result.meta_description,
      main_keyword: result.main_keyword,
      secondary_keywords: result.secondary_keywords,
      slug: result.slug,
      seo_score: result.seo_score,
      analysis: result.analysis
    };

    navigator.clipboard.writeText(JSON.stringify(exportJson, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getScoreColor = (score: number) => {
    if (score >= 90) return "score-excellent";
    if (score >= 70) return "score-good";
    return "score-average";
  };

  const getScoreRating = (score: number) => {
    if (score >= 90) return "Xuất Sắc";
    if (score >= 70) return "Khá";
    return "Cần cải thiện";
  };

  return (
    <div className="output-console-card">
      <div className="console-header">
        <div className="tabs">
          <button 
            className={`tab-btn ${activeTab === "analysis" ? "active" : ""}`}
            onClick={() => setActiveTab("analysis")}
          >
            <BarChart3 size={16} />
            <span>Phân tích SEO</span>
          </button>
          <button 
            className={`tab-btn ${activeTab === "json" ? "active" : ""}`}
            onClick={() => setActiveTab("json")}
          >
            <FileJson size={16} />
            <span>JSON Kết quả</span>
          </button>
        </div>

        <button className="copy-btn" onClick={handleCopy}>
          {copied ? (
            <>
              <Check size={16} className="text-emerald-400" />
              <span className="text-emerald-400">Đã sao chép!</span>
            </>
          ) : (
            <>
              <Copy size={16} />
              <span>Sao chép JSON</span>
            </>
          )}
        </button>
      </div>

      <div className="console-body">
        {activeTab === "analysis" ? (
          <div className="analysis-tab-content">
            {/* Score & Summary Grid */}
            <div className="score-summary-grid">
              <div className="score-dial-wrapper">
                <div className={`score-radial ${getScoreColor(result.seo_score)}`}>
                  <div className="score-inner">
                    <span className="score-number">{result.seo_score}</span>
                    <span className="score-label">ĐIỂM SEO</span>
                  </div>
                </div>
                <div className="score-rating-text">
                  Đánh giá: <strong className={getScoreColor(result.seo_score)}>{getScoreRating(result.seo_score)}</strong>
                </div>
              </div>

              <div className="key-metrics-summary">
                <div className="metric-row">
                  <span className="m-label">Độ dài Title:</span>
                  <span className={`m-val badge-status ${result.seo_title.length >= 50 && result.seo_title.length <= 60 ? "success" : "warning"}`}>
                    {result.seo_title.length} ký tự
                  </span>
                </div>
                <div className="metric-row">
                  <span className="m-label">Độ dài Description:</span>
                  <span className={`m-val badge-status ${result.meta_description.length >= 140 && result.meta_description.length <= 160 ? "success" : "warning"}`}>
                    {result.meta_description.length} ký tự
                  </span>
                </div>
                <div className="metric-row">
                  <span className="m-label">Ước tính CTR:</span>
                  <span className={`m-val badge-status ${result.analysis.ctr === "Cao" ? "success" : "info"}`}>
                    {result.analysis.ctr}
                  </span>
                </div>
                <div className="metric-row slug-row">
                  <span className="m-label">URL Slug:</span>
                  <span className="m-val slug-val" title={result.slug}>
                    {result.slug}
                  </span>
                </div>
              </div>
            </div>

            {/* Detailed Feedback Cards */}
            <div className="feedback-cards-container">
              <div className="feedback-card">
                <div className="feedback-card-header title-color">
                  <h4>Đánh giá Tiêu đề (Title)</h4>
                </div>
                <p className="feedback-text">{result.analysis.title}</p>
              </div>

              <div className="feedback-card">
                <div className="feedback-card-header desc-color">
                  <h4>Đánh giá Mô tả (Meta Description)</h4>
                </div>
                <p className="feedback-text">{result.analysis.description}</p>
              </div>

              <div className="feedback-card suggestion-card">
                <div className="feedback-card-header suggestion-color">
                  <AlertCircle size={16} />
                  <h4>Đề xuất cải thiện</h4>
                </div>
                <p className="feedback-text">{result.analysis.suggestion}</p>
              </div>
            </div>
          </div>
        ) : (
          <div className="json-tab-content">
            <pre className="code-view">
              <code>
{JSON.stringify({
  seo_title: result.seo_title,
  meta_description: result.meta_description,
  main_keyword: result.main_keyword,
  secondary_keywords: result.secondary_keywords,
  slug: result.slug,
  seo_score: result.seo_score,
  analysis: result.analysis
}, null, 2)}
              </code>
            </pre>
          </div>
        )}
      </div>
    </div>
  );
};
