import React, { useState, useEffect } from "react";
import { Settings, Eye, EyeOff, Check, AlertCircle } from "lucide-react";
import type { PipelineConfig } from "../services/seoPipeline";

interface SettingsPanelProps {
  config: PipelineConfig;
  onChange: (newConfig: PipelineConfig) => void;
}

export const SettingsPanel: React.FC<SettingsPanelProps> = ({ config, onChange }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [apiKey, setApiKey] = useState(config.apiKey);
  const [modelName, setModelName] = useState(config.modelName);
  const [isSimulation, setIsSimulation] = useState(config.isSimulation);
  const [brandName, setBrandName] = useState(config.brandName || "");
  const [showKey, setShowKey] = useState(false);
  const [isSaved, setIsSaved] = useState(false);

  useEffect(() => {
    // Load config from localStorage on mount
    const savedKey = localStorage.getItem("gemini_seo_api_key") || "";
    const savedModel = localStorage.getItem("gemini_seo_model") || "gemini-2.5-flash";
    const savedSim = localStorage.getItem("gemini_seo_sim") !== "false"; // default to simulation
    const savedBrand = localStorage.getItem("gemini_seo_brand") || "";

    onChange({
      apiKey: savedKey,
      modelName: savedModel,
      isSimulation: savedSim,
      brandName: savedBrand
    });

    setApiKey(savedKey);
    setModelName(savedModel);
    setIsSimulation(savedSim);
    setBrandName(savedBrand);
  }, []);

  const handleSave = () => {
    localStorage.setItem("gemini_seo_api_key", apiKey);
    localStorage.setItem("gemini_seo_model", modelName);
    localStorage.setItem("gemini_seo_sim", String(isSimulation));
    localStorage.setItem("gemini_seo_brand", brandName);

    onChange({
      apiKey,
      modelName,
      isSimulation,
      brandName
    });

    setIsSaved(true);
    setTimeout(() => setIsSaved(false), 2000);
  };

  return (
    <div className="settings-container">
      <button 
        className={`settings-toggle-btn ${isOpen ? "active" : ""}`}
        onClick={() => setIsOpen(!isOpen)}
        title="Cấu hình API & Pipeline"
      >
        <Settings size={20} className={isOpen ? "spin-icon" : ""} />
        <span>Cấu hình</span>
      </button>

      {isOpen && (
        <div className="settings-backdrop" onClick={() => setIsOpen(false)}>
          <div className="settings-drawer" onClick={(e) => e.stopPropagation()}>
            <div className="settings-header">
              <h3>Cấu hình hệ thống</h3>
              <button className="close-btn" onClick={() => setIsOpen(false)}>&times;</button>
            </div>

            <div className="settings-body">
              {/* Simulation Mode Toggle */}
              <div className="setting-group">
                <label className="toggle-label">
                  <span className="label-text">Chế độ chạy</span>
                  <div className="toggle-switch">
                    <input 
                      type="checkbox"
                      checked={isSimulation}
                      onChange={(e) => setIsSimulation(e.target.checked)}
                    />
                    <span className="slider"></span>
                  </div>
                </label>
                <p className="setting-desc">
                  {isSimulation 
                    ? "Đang chạy chế độ Giả lập (Simulation Mode). Không cần API Key." 
                    : "Đang chạy chế độ Trực tiếp (Live AI Mode). Cần kết nối Gemini API."}
                </p>
              </div>

              {/* API Key */}
              {!isSimulation && (
                <div className="setting-group">
                  <label htmlFor="apiKey" className="field-label">Gemini API Key</label>
                  <div className="password-input-wrapper">
                    <input
                      id="apiKey"
                      type={showKey ? "text" : "password"}
                      value={apiKey}
                      onChange={(e) => setApiKey(e.target.value)}
                      placeholder="AIzaSy..."
                      className="form-input"
                    />
                    <button 
                      type="button" 
                      onClick={() => setShowKey(!showKey)}
                      className="password-toggle"
                    >
                      {showKey ? <EyeOff size={16} /> : <Eye size={16} />}
                    </button>
                  </div>
                  <p className="setting-desc">
                    Lấy khóa tại <a href="https://aistudio.google.com/" target="_blank" rel="noreferrer">Google AI Studio</a>. Khóa được lưu cục bộ trong trình duyệt của bạn.
                  </p>
                </div>
              )}

              {/* Gemini Model */}
              {!isSimulation && (
                <div className="setting-group">
                  <label htmlFor="modelName" className="field-label">Model Generative AI</label>
                  <select
                    id="modelName"
                    value={modelName}
                    onChange={(e) => setModelName(e.target.value)}
                    className="form-select"
                  >
                    <option value="gemini-2.5-flash">Gemini 2.5 Flash (Nhanh & Tối ưu)</option>
                    <option value="gemini-2.5-pro">Gemini 2.5 Pro (Thông minh, Phù hợp phân tích sâu)</option>
                    <option value="gemini-1.5-flash">Gemini 1.5 Flash (Legacy)</option>
                  </select>
                </div>
              )}

              {/* Brand Name Input */}
              <div className="setting-group">
                <label htmlFor="brandName" className="field-label">Thương hiệu mặc định</label>
                <input
                  id="brandName"
                  type="text"
                  value={brandName}
                  onChange={(e) => setBrandName(e.target.value)}
                  placeholder="Ví dụ: BYJANE, Coolmate..."
                  className="form-input"
                />
                <p className="setting-desc">
                  Thương hiệu này sẽ được chèn tự động vào tiêu đề SEO nếu có.
                </p>
              </div>

              {/* Error Warning if Live Mode and No Key */}
              {!isSimulation && !apiKey && (
                <div className="settings-warning">
                  <AlertCircle size={16} />
                  <span>Vui lòng nhập API Key để bắt đầu tối ưu hóa trực tiếp.</span>
                </div>
              )}
            </div>

            <div className="settings-footer">
              <button 
                type="button" 
                onClick={handleSave}
                className="save-settings-btn"
              >
                {isSaved ? (
                  <>
                    <Check size={16} />
                    <span>Đã lưu!</span>
                  </>
                ) : (
                  <span>Lưu thay đổi</span>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
