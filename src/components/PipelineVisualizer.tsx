import React, { useState } from "react";
import { 
  Key, 
  FileText, 
  Type, 
  Award, 
  Loader2, 
  CheckCircle2, 
  AlertTriangle, 
  XCircle, 
  ChevronDown, 
  ChevronUp, 
  Terminal
} from "lucide-react";
import type { PipelineStepUpdate } from "../services/seoPipeline";

interface PipelineVisualizerProps {
  steps: Record<string, PipelineStepUpdate>;
  isProcessing: boolean;
}

export const PipelineVisualizer: React.FC<PipelineVisualizerProps> = ({ steps, isProcessing }) => {
  const [expandedLogs, setExpandedLogs] = useState<Record<string, boolean>>({
    title: true,
    description: true
  });

  const toggleLogs = (stepId: string) => {
    setExpandedLogs(prev => ({
      ...prev,
      [stepId]: !prev[stepId]
    }));
  };

  const getStepIcon = (step: PipelineStepUpdate) => {
    if (step.status === "running") {
      return <Loader2 className="step-spinner animate-spin" size={20} />;
    }
    if (step.status === "success") {
      return <CheckCircle2 className="step-success-icon" size={20} />;
    }
    if (step.status === "warning") {
      return <AlertTriangle className="step-warning-icon" size={20} />;
    }
    if (step.status === "error") {
      return <XCircle className="step-error-icon" size={20} />;
    }
    
    // Default icons for idle state based on step ID
    switch (step.id) {
      case "keywords":
        return <Key size={20} className="step-idle-icon" />;
      case "title":
        return <Type size={20} className="step-idle-icon" />;
      case "description":
        return <FileText size={20} className="step-idle-icon" />;
      case "scoring":
        return <Award size={20} className="step-idle-icon" />;
      default:
        return <Key size={20} className="step-idle-icon" />;
    }
  };

  const renderStepOutput = (step: PipelineStepUpdate) => {
    if (!step.output) return null;

    if (step.id === "keywords") {
      const { mainKeyword, secondaryKeywords, usps } = step.output;
      return (
        <div className="step-output-details">
          <div className="output-item">
            <span className="output-label">Từ khóa chính:</span>
            <span className="output-value main-kw-badge">{mainKeyword}</span>
          </div>
          <div className="output-item">
            <span className="output-label">Từ khóa phụ:</span>
            <div className="keywords-tags">
              {secondaryKeywords.map((kw: string, idx: number) => (
                <span key={idx} className="kw-tag">{kw}</span>
              ))}
            </div>
          </div>
          <div className="output-item">
            <span className="output-label">Ưu điểm nổi bật (USPs):</span>
            <ul className="usps-list">
              {usps.map((usp: string, idx: number) => (
                <li key={idx}>• {usp}</li>
              ))}
            </ul>
          </div>
        </div>
      );
    }

    if (step.id === "title") {
      const title = step.output;
      return (
        <div className="step-output-details">
          <div className="text-preview-box">
            <p className="preview-text">"{title}"</p>
            <span className={`char-counter ${title.length >= 50 && title.length <= 60 ? "valid" : "invalid"}`}>
              {title.length} / 60 ký tự
            </span>
          </div>
        </div>
      );
    }

    if (step.id === "description") {
      const desc = step.output;
      return (
        <div className="step-output-details">
          <div className="text-preview-box">
            <p className="preview-text">"{desc}"</p>
            <span className={`char-counter ${desc.length >= 140 && desc.length <= 160 ? "valid" : "invalid"}`}>
              {desc.length} / 160 ký tự
            </span>
          </div>
        </div>
      );
    }

    return null;
  };

  return (
    <div className="pipeline-visualizer-card">
      <div className="card-header-with-badge">
        <h2>Tiến trình Pipeline SEO</h2>
        {isProcessing && (
          <span className="processing-badge">
            <Loader2 size={12} className="animate-spin" />
            Đang chạy...
          </span>
        )}
      </div>

      <div className="pipeline-flow">
        {Object.values(steps).map((step, index, arr) => {
          const isActive = step.status !== "idle";
          const isCompleted = step.status === "success";
          const hasDetails = !!step.details;
          const isLogOpen = expandedLogs[step.id] ?? false;

          return (
            <div 
              key={step.id} 
              className={`pipeline-node ${step.status} ${isActive ? "active" : ""}`}
            >
              {/* Connector line */}
              {index < arr.length - 1 && (
                <div className={`connector-line ${isCompleted ? "completed" : ""} ${step.status === "running" ? "animating" : ""}`} />
              )}

              <div className="node-icon-wrapper">
                <div className={`node-icon-circle ${step.status}`}>
                  {getStepIcon(step)}
                </div>
                <div className="step-number">{index + 1}</div>
              </div>

              <div className="node-content">
                <div className="node-header">
                  <h4 className="node-title">{step.label}</h4>
                  <span className={`status-badge ${step.status}`}>
                    {step.status === "idle" && "Chờ chạy"}
                    {step.status === "running" && "Đang xử lý"}
                    {step.status === "warning" && "Đang chỉnh sửa"}
                    {step.status === "success" && "Hoàn thành"}
                    {step.status === "error" && "Gặp lỗi"}
                  </span>
                </div>

                <p className="node-message">{step.message}</p>

                {/* Display step outputs if available */}
                {renderStepOutput(step)}

                {/* Self-correction logs */}
                {hasDetails && (
                  <div className="correction-logs-container">
                    <button 
                      type="button"
                      className="toggle-logs-btn"
                      onClick={() => toggleLogs(step.id)}
                    >
                      <Terminal size={14} />
                      <span>Nhật ký tự sửa lỗi ({step.id === 'title' ? 'Title' : 'Description'})</span>
                      {isLogOpen ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                    </button>
                    
                    {isLogOpen && (
                      <pre className="terminal-logs">
                        <code>{step.details}</code>
                      </pre>
                    )}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
