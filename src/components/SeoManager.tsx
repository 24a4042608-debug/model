import React, { useState } from "react";
import { Sparkles, Edit2, Trash2, CheckCircle, AlertTriangle, AlertCircle, FileText } from "lucide-react";

interface SeoProduct {
  product_id: string;
  seo_title: string;
  meta_description: string;
  slug: string;
  main_keyword: string;
  secondary_keywords: string[];
  usp: string[];
  target_customer?: string;
  search_intent?: string;
  seo_score: number;
  analysis: {
    title?: string;
    description?: string;
    ctr?: string;
    suggestion?: string;
  };
}

interface SeoManagerProps {
  products: SeoProduct[];
  onUpdate: (productId: string, data: any) => Promise<void>;
  onDelete: (productId: string) => Promise<void>;
  isProcessing: boolean;
}

export const SeoManager: React.FC<SeoManagerProps> = ({
  products,
  onUpdate,
  onDelete,
  isProcessing
}) => {
  const [editingProduct, setEditingProduct] = useState<SeoProduct | null>(null);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showAnalysisModal, setShowAnalysisModal] = useState<SeoProduct | null>(null);

  // Form states
  const [formTitle, setFormTitle] = useState("");
  const [formDesc, setFormDesc] = useState("");
  const [formSlug, setFormSlug] = useState("");
  const [formMainKw, setFormMainKw] = useState("");
  const [formSecondaryKws, setFormSecondaryKws] = useState("");
  const [formUsps, setFormUsps] = useState("");
  const [formCustomer, setFormCustomer] = useState("");
  const [formIntent, setFormIntent] = useState("");
  const [formScore, setFormScore] = useState(0);

  const openEditModal = (prod: SeoProduct) => {
    setEditingProduct(prod);
    setFormTitle(prod.seo_title);
    setFormDesc(prod.meta_description);
    setFormSlug(prod.slug);
    setFormMainKw(prod.main_keyword);
    setFormSecondaryKws(prod.secondary_keywords.join(", "));
    setFormUsps(prod.usp.join(", "));
    setFormCustomer(prod.target_customer || "");
    setFormIntent(prod.search_intent || "");
    setFormScore(prod.seo_score);
    setShowEditModal(true);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingProduct) return;

    const payload = {
      seo_title: formTitle,
      meta_description: formDesc,
      slug: formSlug,
      main_keyword: formMainKw,
      secondary_keywords: formSecondaryKws.split(",").map(k => k.trim()).filter(Boolean),
      usp: formUsps.split(",").map(u => u.trim()).filter(Boolean),
      target_customer: formCustomer,
      search_intent: formIntent,
      seo_score: Number(formScore)
    };

    await onUpdate(editingProduct.product_id, payload);
    setShowEditModal(false);
  };

  const getScoreColor = (score: number) => {
    if (score >= 90) return "text-emerald-400 bg-emerald-500/10 border-emerald-500/20";
    if (score >= 70) return "text-amber-400 bg-amber-500/10 border-amber-500/20";
    return "text-red-400 bg-red-500/10 border-red-500/20";
  };

  // Simple Frontend validator checklist helper
  const runValidatorChecklist = (prod: SeoProduct) => {
    const checks = [
      {
        label: "Độ dài tiêu đề (50 - 60 ký tự)",
        status: prod.seo_title.length >= 50 && prod.seo_title.length <= 60,
        desc: `Hiện tại: ${prod.seo_title.length} ký tự`
      },
      {
        label: "Từ khóa chính ở đầu tiêu đề",
        status: prod.seo_title.toLowerCase().startsWith(prod.main_keyword.toLowerCase()),
        desc: `Từ khóa: "${prod.main_keyword}"`
      },
      {
        label: "Độ dài mô tả (140 - 160 ký tự)",
        status: prod.meta_description.length >= 140 && prod.meta_description.length <= 160,
        desc: `Hiện tại: ${prod.meta_description.length} ký tự`
      },
      {
        label: "Có CTA (Lời kêu gọi hành động) trong mô tả",
        status: ["mua ngay", "khám phá", "đặt hàng", "xem ngay"].some(cta => prod.meta_description.toLowerCase().includes(cta)),
        desc: "Kiểm tra từ khóa kích thích mua hàng"
      },
      {
        label: "Không chứa ký tự spam (★, !!!, >>>)",
        status: !["★", "!!!", ">>>"].some(spam => prod.seo_title.includes(spam) || prod.meta_description.includes(spam)),
        desc: "Sạch ký tự quảng cáo rác"
      }
    ];
    return checks;
  };

  return (
    <div className="manager-section">
      <div className="section-card input-panel-card">
        <div className="panel-header justify-between">
          <div className="flex items-center gap-2">
            <Sparkles size={20} className="header-icon text-violet-400" />
            <h2>Dữ liệu SEO Tối ưu hóa ({products.length})</h2>
          </div>
        </div>

        {products.length === 0 ? (
          <div className="empty-state py-12">
            <AlertCircle size={32} className="text-zinc-500 mb-2" />
            <p className="text-zinc-400 text-sm">Chưa có sản phẩm nào được tối ưu SEO. Hãy chọn tối ưu ở màn hình Crawl.</p>
          </div>
        ) : (
          <div className="table-responsive">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Product ID</th>
                  <th>Tiêu đề SEO (Title) / Slug</th>
                  <th>Từ khóa chính</th>
                  <th>Điểm SEO</th>
                  <th className="actions-header">Hành động</th>
                </tr>
              </thead>
              <tbody>
                {products.map((prod) => {
                  const checklist = runValidatorChecklist(prod);
                  const failCount = checklist.filter(c => !c.status).length;

                  return (
                    <tr key={prod.product_id}>
                      <td className="font-mono text-xs text-zinc-400">{prod.product_id}</td>
                      <td>
                        <div className="font-semibold text-sm max-w-sm truncate" title={prod.seo_title}>
                          {prod.seo_title}
                        </div>
                        <div className="text-xs font-mono text-sky-400 mt-xs truncate max-w-xs">{prod.slug}</div>
                      </td>
                      <td>
                        <span className="main-kw-badge text-xs">{prod.main_keyword}</span>
                      </td>
                      <td>
                        <div className="flex items-center gap-2">
                          <span className={`px-2 py-0.5 rounded-full border text-xs font-bold ${getScoreColor(prod.seo_score)}`}>
                            {prod.seo_score}/100
                          </span>
                          {failCount > 0 ? (
                            <span className="flex items-center text-amber-400" title={`Lỗi checklist: ${failCount}`}>
                              <AlertTriangle size={12} />
                            </span>
                          ) : (
                            <span className="flex items-center text-emerald-400" title="Đạt mọi tiêu chuẩn">
                              <CheckCircle size={12} />
                            </span>
                          )}
                        </div>
                      </td>
                      <td>
                        <div className="table-actions">

                          <button
                            className="action-btn text-violet-400 hover:bg-violet-500/10"
                            title="Báo cáo SEO"
                            onClick={() => setShowAnalysisModal(prod)}
                            disabled={isProcessing}
                          >
                            <FileText size={14} />
                          </button>
                          <button
                            className="action-btn text-zinc-400 hover:bg-zinc-500/10"
                            title="Sửa"
                            onClick={() => openEditModal(prod)}
                            disabled={isProcessing}
                          >
                            <Edit2 size={14} />
                          </button>
                          <button
                            className="action-btn text-red-400 hover:bg-red-500/10"
                            title="Xóa"
                            onClick={() => onDelete(prod.product_id)}
                            disabled={isProcessing}
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Edit SEO Modal */}
      {showEditModal && editingProduct && (
        <div className="modal-backdrop" onClick={() => setShowEditModal(false)}>
          <div className="modal-container max-w-xl" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Hiệu chỉnh Dữ liệu SEO</h3>
              <button className="close-btn" onClick={() => setShowEditModal(false)}>&times;</button>
            </div>
            <form onSubmit={handleSave} className="modal-form">
              <div className="form-group">
                <label className="field-label-required">Tiêu đề SEO</label>
                <input
                  type="text"
                  value={formTitle}
                  onChange={(e) => setFormTitle(e.target.value)}
                  className="form-input"
                  required
                />
                <span className={`text-xs self-end mt-1 ${formTitle.length >= 50 && formTitle.length <= 60 ? "text-emerald-400" : "text-amber-400"}`}>
                  {formTitle.length} / 60 ký tự (Chuẩn: 50-60)
                </span>
              </div>

              <div className="form-group">
                <label className="field-label-required">Mô tả Meta Description</label>
                <textarea
                  value={formDesc}
                  onChange={(e) => setFormDesc(e.target.value)}
                  className="form-textarea"
                  rows={4}
                  required
                />
                <span className={`text-xs self-end mt-1 ${formDesc.length >= 140 && formDesc.length <= 160 ? "text-emerald-400" : "text-amber-400"}`}>
                  {formDesc.length} / 160 ký tự (Chuẩn: 140-160)
                </span>
              </div>

              <div className="form-row">
                <div className="form-group flex-1">
                  <label className="field-label">URL Slug</label>
                  <input
                    type="text"
                    value={formSlug}
                    onChange={(e) => setFormSlug(e.target.value)}
                    className="form-input font-mono text-sm"
                  />
                </div>
                <div className="form-group flex-1">
                  <label className="field-label">Điểm SEO</label>
                  <input
                    type="number"
                    value={formScore}
                    onChange={(e) => setFormScore(Number(e.target.value))}
                    className="form-input"
                    max={100}
                    min={0}
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="field-label">Từ khóa chính</label>
                <input
                  type="text"
                  value={formMainKw}
                  onChange={(e) => setFormMainKw(e.target.value)}
                  className="form-input"
                />
              </div>

              <div className="form-group">
                <label className="field-label">Từ khóa phụ (cách nhau bằng dấu phẩy)</label>
                <input
                  type="text"
                  value={formSecondaryKws}
                  onChange={(e) => setFormSecondaryKws(e.target.value)}
                  className="form-input"
                />
              </div>

              <div className="form-group">
                <label className="field-label">Ưu điểm nổi bật (USPs - cách nhau bằng dấu phẩy)</label>
                <input
                  type="text"
                  value={formUsps}
                  onChange={(e) => setFormUsps(e.target.value)}
                  className="form-input"
                />
              </div>

              <div className="form-row">
                <div className="form-group flex-1">
                  <label className="field-label">Khách hàng mục tiêu</label>
                  <input
                    type="text"
                    value={formCustomer}
                    onChange={(e) => setFormCustomer(e.target.value)}
                    className="form-input text-xs"
                  />
                </div>
                <div className="form-group flex-1">
                  <label className="field-label">Ý định tìm kiếm</label>
                  <input
                    type="text"
                    value={formIntent}
                    onChange={(e) => setFormIntent(e.target.value)}
                    className="form-input text-xs"
                  />
                </div>
              </div>

              <div className="modal-footer">
                <button type="button" className="btn-secondary" onClick={() => setShowEditModal(false)}>Hủy</button>
                <button type="submit" className="btn-primary">Lưu thay đổi</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Review Audit Analysis Report Modal */}
      {showAnalysisModal && (
        <div className="modal-backdrop" onClick={() => setShowAnalysisModal(null)}>
          <div className="modal-container max-w-lg" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Báo Cáo Kiểm Toán SEO</h3>
              <button className="close-btn" onClick={() => setShowAnalysisModal(null)}>&times;</button>
            </div>
            <div className="modal-body p-4 flex flex-col gap-4">
              <div className="flex justify-between items-center bg-zinc-800/30 p-3 rounded-lg border border-zinc-700/20">
                <span className="font-semibold text-zinc-300">Điểm SEO Đánh Giá:</span>
                <span className={`px-2 py-0.5 rounded-full border text-xs font-bold ${getScoreColor(showAnalysisModal.seo_score)}`}>
                  {showAnalysisModal.seo_score}/100
                </span>
              </div>

              <div className="flex flex-col gap-2">
                <span className="font-semibold text-xs text-zinc-400 uppercase tracking-wider">Bộ lọc kiểm tra (SEO Rules)</span>
                <div className="flex flex-col gap-2">
                  {runValidatorChecklist(showAnalysisModal).map((chk, idx) => (
                    <div key={idx} className="flex justify-between items-center bg-zinc-900/40 p-2 rounded border border-zinc-800/40">
                      <div className="flex items-center gap-2">
                        {chk.status ? (
                          <CheckCircle size={14} className="text-emerald-400" />
                        ) : (
                          <AlertTriangle size={14} className="text-amber-400" />
                        )}
                        <span className="text-xs text-zinc-300">{chk.label}</span>
                      </div>
                      <span className="text-xxs text-zinc-500 font-mono">{chk.desc}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex flex-col gap-2 mt-2">
                <span className="font-semibold text-xs text-zinc-400 uppercase tracking-wider">Đánh giá chi tiết từ AI</span>
                <div className="flex flex-col gap-3">
                  <div className="bg-violet-950/15 border border-violet-900/20 p-3 rounded-lg">
                    <h5 className="text-xs font-bold text-violet-400 mb-1">Kiểm tra Tiêu đề</h5>
                    <p className="text-xs text-zinc-400 leading-relaxed">{showAnalysisModal.analysis.title || "Rất tốt."}</p>
                  </div>
                  <div className="bg-sky-950/15 border border-sky-900/20 p-3 rounded-lg">
                    <h5 className="text-xs font-bold text-sky-400 mb-1">Kiểm tra Mô tả</h5>
                    <p className="text-xs text-zinc-400 leading-relaxed">{showAnalysisModal.analysis.description || "Đầy đủ CTA."}</p>
                  </div>
                  <div className="bg-amber-950/15 border border-amber-900/20 p-3 rounded-lg">
                    <h5 className="text-xs font-bold text-amber-400 mb-1 flex items-center gap-1">
                      <AlertCircle size={12} />
                      Đề xuất cải tiến
                    </h5>
                    <p className="text-xs text-zinc-400 leading-relaxed">{showAnalysisModal.analysis.suggestion || "Không có đề xuất thêm."}</p>
                  </div>
                </div>
              </div>
            </div>
            <div className="modal-footer">
              <button type="button" className="btn-secondary" onClick={() => setShowAnalysisModal(null)}>Đóng</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
