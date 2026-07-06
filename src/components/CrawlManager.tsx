import React, { useState } from "react";
import { Plus, Edit2, Trash2, Sparkles, AlertCircle, Store } from "lucide-react";

interface RawProduct {
  id: number;
  product_id: string;
  title: string;
  description: string;
  price: number;
  brand: string;
  images: string[];
  url: string;
  category?: string;
  price_text?: string;
  created_at?: string;
  rating_star?: number;
  sold_count?: number;
  video?: string;
}

interface CrawlManagerProps {
  products: RawProduct[];
  onAdd: (data: any) => Promise<void>;
  onUpdate: (id: number, data: any) => Promise<void>;
  onDelete: (id: number) => Promise<void>;
  onCrawl: (url: string, method?: string, cookie?: string) => Promise<void>;
  onCrawlShop: (url: string, method?: string, cookie?: string, maxProducts?: number) => Promise<void>;
  onCrawlActiveTab: () => Promise<void>;
  onTriggerSeo: (productId: string) => Promise<void>;
  isProcessing: boolean;
  activeTaskId: string | null;
  apiUrl: string;
  isSimulation: boolean;
  onRefreshData: () => Promise<void>;
}

export const CrawlManager: React.FC<CrawlManagerProps> = ({
  products,
  onAdd,
  onUpdate,
  onDelete,
  onTriggerSeo,
  isProcessing,
  apiUrl,
  isSimulation,
  onRefreshData
}) => {
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingProduct, setEditingProduct] = useState<RawProduct | null>(null);

  // Form states
  const [formId, setFormId] = useState("");
  const [formTitle, setFormTitle] = useState("");
  const [formDesc, setFormDesc] = useState("");
  const [formPrice, setFormPrice] = useState(0);
  const [formBrand, setFormBrand] = useState("");
  const [formUrl, setFormUrl] = useState("");
  const [formImage, setFormImage] = useState("");
  const [formCategory, setFormCategory] = useState("");
  const [formRatingStar, setFormRatingStar] = useState<number | "">("");
  const [formSoldCount, setFormSoldCount] = useState<number | "">("");
  const [formVideo, setFormVideo] = useState("");
  const [formAdditionalImages, setFormAdditionalImages] = useState<string[]>([]);
  const [isUploading, setIsUploading] = useState(false);

  const handleClearAll = async () => {
    if (!window.confirm("Bạn có chắc chắn muốn xóa tất cả sản phẩm?")) {
      return;
    }
    
    try {
      if (isSimulation) {
        localStorage.removeItem("sim_raw_products");
        await onRefreshData();
        alert("Đã xóa tất cả dữ liệu (Simulation Mode)");
        return;
      }
      
      const res = await fetch(`${apiUrl}/api/raw-products`, {
        method: "DELETE"
      });
      
      if (res.ok) {
        await onRefreshData();
        alert("Đã xóa tất cả sản phẩm trong database thành công!");
      } else {
        alert("Có lỗi xảy ra khi xóa dữ liệu.");
      }
    } catch (e) {
      console.error(e);
      alert("Không thể kết nối đến API Server.");
    }
  };

  const handleFileUpload = async (file: File): Promise<string | null> => {
    setIsUploading(true);
    const formData = new FormData();
    formData.append("file", file);
    try {
      const res = await fetch(`${apiUrl}/api/upload`, {
        method: "POST",
        body: formData
      });
      if (res.ok) {
        const data = await res.json();
        return data.url;
      } else {
        alert("Upload file thất bại!");
        return null;
      }
    } catch (e) {
      console.error(e);
      alert("Lỗi kết nối khi upload file.");
      return null;
    } finally {
      setIsUploading(false);
    }
  };

  const handleMainImageChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const url = await handleFileUpload(file);
    if (url) {
      setFormImage(url);
    }
  };

  const handleAdditionalImageChange = async (idx: number, e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const url = await handleFileUpload(file);
    if (url) {
      const updated = [...formAdditionalImages];
      updated[idx] = url;
      setFormAdditionalImages(updated);
    }
  };

  const handleVideoChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const url = await handleFileUpload(file);
    if (url) {
      setFormVideo(url);
    }
  };

  const removeAdditionalImage = (idx: number) => {
    const updated = [...formAdditionalImages];
    updated[idx] = "";
    setFormAdditionalImages(updated.filter(img => img !== ""));
  };

  const openAddModal = () => {
    setFormId("prod_" + Math.random().toString(36).substr(2, 9));
    setFormTitle("");
    setFormDesc("");
    setFormPrice(290000);
    setFormBrand("");
    setFormUrl("");
    setFormImage("https://picsum.photos/400/400");
    setFormCategory("");
    setFormRatingStar("");
    setFormSoldCount("");
    setFormVideo("");
    setFormAdditionalImages([]);
    setEditingProduct(null);
    setShowAddModal(true);
  };

  const openEditModal = (prod: RawProduct) => {
    setEditingProduct(prod);
    setFormId(prod.product_id);
    setFormTitle(prod.title);
    setFormDesc(prod.description);
    setFormPrice(prod.price);
    setFormBrand(prod.brand);
    setFormUrl(prod.url);
    setFormImage(prod.images[0] || "");
    setFormCategory(prod.category || "");
    setFormRatingStar(prod.rating_star ?? "");
    setFormSoldCount(prod.sold_count ?? "");
    setFormVideo(prod.video || "");
    setFormAdditionalImages(prod.images.slice(1) || []);
    setShowAddModal(true);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    const payload = {
      product_id: formId,
      title: formTitle,
      description: formDesc,
      price: Number(formPrice),
      brand: formBrand,
      url: formUrl,
      images: [formImage, ...formAdditionalImages].filter(img => img && img.trim() !== ""),
      category: formCategory,
      rating_star: formRatingStar !== "" ? Number(formRatingStar) : null,
      sold_count: formSoldCount !== "" ? Number(formSoldCount) : null,
      video: formVideo
    };

    if (editingProduct) {
      await onUpdate(editingProduct.id, payload);
    } else {
      await onAdd(payload);
    }
    setShowAddModal(false);
  };

  return (
    <div className="manager-section">
      {/* Raw Products list */}
      <div className="section-card input-panel-card">
        <div className="panel-header justify-between">
          <div className="flex items-center gap-2">
            <Store size={20} className="header-icon text-emerald-400" />
            <h2>Danh sách Sản phẩm ({products.length})</h2>
          </div>
          <div className="flex items-center gap-2">
            {products.length > 0 && (
              <button 
                className="btn-danger py-sm px-3 text-xs flex items-center gap-1"
                onClick={handleClearAll}
                disabled={isProcessing}
                style={{
                  backgroundColor: "rgba(239, 68, 68, 0.1)",
                  color: "#ef4444",
                  border: "1px solid rgba(239, 68, 68, 0.3)",
                  borderRadius: "6px",
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center"
                }}
              >
                <Trash2 size={14} />
                <span>Xóa tất cả</span>
              </button>
            )}
            <button className="btn-secondary py-sm px-3 text-xs" onClick={openAddModal} disabled={isProcessing}>
              <Plus size={14} />
              <span>Thêm thủ công</span>
            </button>
          </div>
        </div>

        {products.length === 0 ? (
          <div className="empty-state">
            <AlertCircle size={32} className="text-zinc-500 mb-2" />
            <p className="text-zinc-400 text-sm">Chưa có sản phẩm nào trong kho hàng.</p>
          </div>
        ) : (
          <div className="table-responsive">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Hình ảnh</th>
                  <th>ID sản phẩm</th>
                  <th>Tên sản phẩm / Thương hiệu</th>
                  <th>Giá (VNĐ)</th>
                  <th>Đánh giá</th>
                  <th>Đã bán</th>
                  <th>Danh mục</th>
                  <th>Mô tả ngắn</th>
                  <th>Link gốc</th>
                  <th>Thời gian cào</th>
                  <th className="actions-header">Hành động</th>
                </tr>
              </thead>
              <tbody>
                {products.map((prod) => (
                  <tr key={prod.id}>
                    <td>
                      <img 
                        src={prod.images?.[0] || "https://picsum.photos/50/50"} 
                        alt={prod.title} 
                        className="table-thumbnail-img"
                        onError={(e) => {
                          (e.target as HTMLImageElement).src = "https://picsum.photos/50/50";
                        }}
                      />
                    </td>
                    <td className="font-mono text-xs text-zinc-400">{prod.product_id}</td>
                    <td>
                      <div className="font-semibold text-sm max-w-sm truncate" title={prod.title}>
                        {prod.title}
                      </div>
                      <span className="text-xs text-zinc-500">Brand: {prod.brand || "Không rõ"}</span>
                    </td>
                    <td className="font-semibold text-sm text-emerald-400">
                      {prod.price_text || (prod.price ? prod.price.toLocaleString("vi-VN") + "đ" : "0đ")}
                    </td>
                    <td>
                      {prod.rating_star ? (
                        <div className="flex items-center gap-1 text-xs text-yellow-400">
                          <span>⭐</span>
                          <span>{prod.rating_star.toFixed(1)}</span>
                        </div>
                      ) : (
                        <span className="text-zinc-600">—</span>
                      )}
                    </td>
                    <td className="text-xs font-semibold text-zinc-300">
                      {prod.sold_count ? (
                        prod.sold_count >= 1000 ? 
                          (prod.sold_count / 1000).toFixed(1) + "k+" : 
                          prod.sold_count
                      ) : (
                        <span className="text-zinc-600">—</span>
                      )}
                    </td>
                    <td>
                      <span className="text-xs text-zinc-500 max-w-xs truncate block" title={prod.category}>
                        {prod.category || "—"}
                      </span>
                    </td>
                    <td>
                      <span className="text-xs text-zinc-500 max-w-xs truncate block" title={prod.description}>
                        {prod.description || "—"}
                      </span>
                    </td>
                    <td>
                      {prod.url ? (
                        <a 
                          href={prod.url} 
                          target="_blank" 
                          rel="noopener noreferrer" 
                          className="text-xs text-sky-400 hover:underline block max-w-[120px] truncate"
                          title={prod.url}
                        >
                          Xem sản phẩm
                        </a>
                      ) : "—"}
                    </td>
                    <td className="text-xs text-zinc-500 font-mono">
                      {prod.created_at ? new Date(prod.created_at).toLocaleString("vi-VN") : "—"}
                    </td>
                    <td>
                      <div className="table-actions">
                        <button
                          className="action-btn text-violet-400 hover:bg-violet-500/10"
                          title="Tối ưu hóa SEO"
                          onClick={() => onTriggerSeo(prod.product_id)}
                          disabled={isProcessing}
                        >
                          <Sparkles size={14} />
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
                          onClick={() => onDelete(prod.id)}
                          disabled={isProcessing}
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Add/Edit Modal */}
      {showAddModal && (
        <div className="modal-backdrop" onClick={() => setShowAddModal(false)}>
          <div className="modal-container" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{editingProduct ? "Cập nhật sản phẩm" : "Thêm sản phẩm mới"}</h3>
              <button className="close-btn" onClick={() => setShowAddModal(false)}>&times;</button>
            </div>
            <form onSubmit={handleSave} className="modal-form">
              <div className="form-group">
                <label className="field-label-required">ID sản phẩm</label>
                <input
                  type="text"
                  value={formId}
                  onChange={(e) => setFormId(e.target.value)}
                  className="form-input"
                  required
                  disabled={!!editingProduct}
                />
              </div>

              <div className="form-group">
                <label className="field-label-required">Tên sản phẩm</label>
                <input
                  type="text"
                  value={formTitle}
                  onChange={(e) => setFormTitle(e.target.value)}
                  className="form-input"
                  required
                />
              </div>

              <div className="form-group">
                <label className="field-label">Mô tả sản phẩm</label>
                <textarea
                  value={formDesc}
                  onChange={(e) => setFormDesc(e.target.value)}
                  className="form-textarea"
                  rows={4}
                />
              </div>

              <div className="form-row">
                <div className="form-group flex-1">
                  <label className="field-label">Giá bán (VNĐ)</label>
                  <input
                    type="number"
                    value={formPrice}
                    onChange={(e) => setFormPrice(Number(e.target.value))}
                    className="form-input"
                  />
                </div>
                <div className="form-group flex-1">
                  <label className="field-label">Thương hiệu</label>
                  <input
                    type="text"
                    value={formBrand}
                    onChange={(e) => setFormBrand(e.target.value)}
                    className="form-input"
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="field-label font-semibold text-violet-400">Ảnh đại diện (Hình 1 - Ảnh chính)</label>
                <div className="flex gap-3 items-center">
                  {formImage && (
                    <div className="w-16 h-16 rounded border border-zinc-800 overflow-hidden flex-shrink-0 bg-zinc-950">
                      <img 
                        src={formImage.startsWith("/") ? `${apiUrl}${formImage}` : formImage} 
                        alt="Ảnh chính" 
                        className="w-full h-full object-cover"
                      />
                    </div>
                  )}
                  <div className="flex-1 flex flex-col gap-1.5">
                    <input
                      type="text"
                      value={formImage}
                      onChange={(e) => setFormImage(e.target.value)}
                      placeholder="Nhập URL ảnh hoặc tải tệp lên..."
                      className="form-input text-xs"
                    />
                    <div className="flex items-center gap-2">
                      <input
                        type="file"
                        accept="image/*"
                        onChange={handleMainImageChange}
                        id="main-image-upload"
                        className="hidden"
                      />
                      <label 
                        htmlFor="main-image-upload"
                        className="btn-secondary py-1 px-3 text-xs cursor-pointer border border-zinc-800 hover:bg-zinc-800 text-zinc-300 rounded"
                      >
                        {isUploading ? "Đang tải..." : "Tải ảnh chính lên"}
                      </label>
                      {formImage && (
                        <button 
                          type="button" 
                          onClick={() => setFormImage("")}
                          className="text-xxs text-red-400 hover:underline"
                        >
                          Xóa ảnh
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              <div className="form-group mt-3">
                <label className="field-label font-semibold text-zinc-400">Ảnh phụ (Tối đa 4 ảnh)</label>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-1.5">
                  {[0, 1, 2, 3].map((idx) => {
                    const imgUrl = formAdditionalImages[idx] || "";
                    return (
                      <div key={idx} className="border border-zinc-800/80 rounded-lg p-2 bg-zinc-900/20 flex flex-col items-center gap-2 justify-center min-h-[100px] relative group">
                        {imgUrl ? (
                          <>
                            <div className="w-12 h-12 rounded border border-zinc-800 overflow-hidden bg-zinc-950">
                              <img 
                                src={imgUrl.startsWith("/") ? `${apiUrl}${imgUrl}` : imgUrl} 
                                alt={`Ảnh phụ ${idx + 1}`} 
                                className="w-full h-full object-cover"
                              />
                            </div>
                            <button
                              type="button"
                              onClick={() => removeAdditionalImage(idx)}
                              className="text-[10px] text-red-400 hover:underline mt-1"
                            >
                              Xóa ảnh
                            </button>
                          </>
                        ) : (
                          <>
                            <input
                              type="file"
                              accept="image/*"
                              onChange={(e) => handleAdditionalImageChange(idx, e)}
                              id={`add-image-upload-${idx}`}
                              className="hidden"
                            />
                            <label 
                              htmlFor={`add-image-upload-${idx}`}
                              className="text-xxs border border-dashed border-zinc-700 hover:border-violet-500 hover:text-violet-400 cursor-pointer p-2 rounded text-zinc-500 text-center w-full h-full flex items-center justify-center min-h-[48px]"
                            >
                              + Tải ảnh {idx + 1}
                            </label>
                          </>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>

              <div className="form-group">
                <label className="field-label">Đường dẫn sản phẩm</label>
                <input
                  type="url"
                  value={formUrl}
                  onChange={(e) => setFormUrl(e.target.value)}
                  className="form-input"
                />
              </div>

              <div className="form-row">
                <div className="form-group flex-1">
                  <label className="field-label">Danh mục</label>
                  <input
                    type="text"
                    value={formCategory}
                    onChange={(e) => setFormCategory(e.target.value)}
                    placeholder="Ví dụ: Thời Trang Nữ > Áo"
                    className="form-input"
                  />
                </div>
                <div className="form-group flex-1">
                  <label className="field-label font-semibold text-violet-400">Video giới thiệu</label>
                  <div className="flex gap-2 items-center">
                    {formVideo && (
                      <div className="w-16 h-12 rounded border border-zinc-800 overflow-hidden flex-shrink-0 bg-zinc-950 flex items-center justify-center">
                        <video 
                          src={formVideo.startsWith("/") ? `${apiUrl}${formVideo}` : formVideo} 
                          className="w-full h-full object-cover"
                        />
                      </div>
                    )}
                    <div className="flex-1 flex flex-col gap-1">
                      <input
                        type="text"
                        value={formVideo}
                        onChange={(e) => setFormVideo(e.target.value)}
                        placeholder="URL video hoặc tải tệp ở dưới..."
                        className="form-input text-xs"
                      />
                      <div className="flex items-center gap-2">
                        <input
                          type="file"
                          accept="video/*"
                          onChange={handleVideoChange}
                          id="video-upload-input"
                          className="hidden"
                        />
                        <label 
                          htmlFor="video-upload-input"
                          className="btn-secondary py-1 px-3 text-[10px] cursor-pointer border border-zinc-800 hover:bg-zinc-800 text-zinc-300 rounded"
                        >
                          Tải video lên
                        </label>
                        {formVideo && (
                          <button 
                            type="button" 
                            onClick={() => setFormVideo("")}
                            className="text-xxs text-red-400 hover:underline"
                          >
                            Xóa video
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="form-row">
                <div className="form-group flex-1">
                  <label className="field-label">Đánh giá (Số sao)</label>
                  <input
                    type="number"
                    min="0"
                    max="5"
                    step="0.1"
                    value={formRatingStar}
                    onChange={(e) => setFormRatingStar(e.target.value === "" ? "" : Number(e.target.value))}
                    placeholder="Ví dụ: 4.8"
                    className="form-input"
                  />
                </div>
                <div className="form-group flex-1">
                  <label className="field-label">Số lượng đã bán</label>
                  <input
                    type="number"
                    min="0"
                    value={formSoldCount}
                    onChange={(e) => setFormSoldCount(e.target.value === "" ? "" : Number(e.target.value))}
                    placeholder="Ví dụ: 150"
                    className="form-input"
                  />
                </div>
              </div>

              <div className="modal-footer">
                <button type="button" className="btn-secondary" onClick={() => setShowAddModal(false)}>Hủy</button>
                <button type="submit" className="btn-primary">Lưu thay đổi</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
