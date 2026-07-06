import React, { useState } from "react";
import { Copy, Edit2, Trash2, Send, CheckCircle2, AlertCircle, Loader2, Terminal, RefreshCw, Globe } from "lucide-react";

interface FacebookPost {
  product_id: string;
  caption: string;
  hashtags: string[];
  status: string; // Pending, Publishing, Posted, Failed
  retry: number;
  posted_at?: string;
  created_at?: string;
}

interface FacebookQueueManagerProps {
  posts: FacebookPost[];
  onUpdate: (productId: string, data: any) => Promise<void>;
  onDelete: (productId: string) => Promise<void>;
  onPublish: (productId: string, fanpageUrl?: string) => Promise<void>;
  isProcessing: boolean;
  activeTaskId: string | null;
  logs: string[];
  onClearLogs: () => void;
}

export const FacebookQueueManager: React.FC<FacebookQueueManagerProps> = ({
  posts,
  onUpdate,
  onDelete,
  onPublish,
  isProcessing,
  activeTaskId: _activeTaskId,
  logs,
  onClearLogs
}) => {
  const [editingPost, setEditingPost] = useState<FacebookPost | null>(null);
  const [showEditModal, setShowEditModal] = useState(false);
  const [formCaption, setFormCaption] = useState("");
  const [formStatus, setFormStatus] = useState("Pending");
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [fanpageUrl, setFanpageUrl] = useState(() => {
    return localStorage.getItem("auto_fb_fanpage_url") || "";
  });
  const [isSaved, setIsSaved] = useState(false);

  const handleSaveFanpageUrl = () => {
    localStorage.setItem("auto_fb_fanpage_url", fanpageUrl);
    setIsSaved(true);
    setTimeout(() => setIsSaved(false), 2000);
  };

  const handleCopy = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const openEditModal = (post: FacebookPost) => {
    setEditingPost(post);
    setFormCaption(post.caption);
    setFormStatus(post.status);
    setShowEditModal(true);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingPost) return;

    await onUpdate(editingPost.product_id, {
      caption: formCaption,
      status: formStatus
    });
    setShowEditModal(false);
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "Posted":
        return <span className="status-badge success border border-emerald-500/20">Đã đăng</span>;
      case "Publishing":
        return (
          <span className="status-badge running border border-violet-500/20 flex items-center gap-1">
            <Loader2 size={10} className="animate-spin" />
            Đang đăng
          </span>
        );
      case "Failed":
        return <span className="status-badge error border border-red-500/20">Lỗi đăng</span>;
      default:
        return <span className="status-badge idle border border-zinc-500/20">Đang chờ</span>;
    }
  };

  return (
    <div className="manager-section grid grid-cols-1 gap-6">
      {/* Configuration Card */}
      <div className="section-card input-panel-card mb-0">
        <div className="panel-header justify-between">
          <div className="flex items-center gap-2">
            <Globe size={20} className="header-icon text-violet-400" />
            <h2>Cấu hình Fanpage Facebook mục tiêu</h2>
          </div>
        </div>
        <div className="flex items-end gap-3 mt-3">
          <div className="flex-1">
            <label className="field-label">Đường dẫn Fanpage (Facebook Fanpage URL)</label>
            <input
              type="text"
              value={fanpageUrl}
              onChange={(e) => setFanpageUrl(e.target.value)}
              placeholder="Ví dụ: https://www.facebook.com/byjane.hn hoặc ID: https://facebook.com/10006371..."
              className="form-input text-zinc-100"
            />
          </div>
          <button 
            onClick={handleSaveFanpageUrl} 
            className="btn-primary py-sm px-6 h-[42px]"
          >
            {isSaved ? "Đã Lưu!" : "Lưu Cấu Hình"}
          </button>
        </div>
      </div>

      {/* Queue list card */}
      <div className="section-card input-panel-card">
        <div className="panel-header justify-between">
          <div className="flex items-center gap-2">
            <Send size={20} className="header-icon text-sky-400" />
            <h2>Hàng đợi Đăng bài Facebook ({posts.length})</h2>
          </div>
        </div>

        {posts.length === 0 ? (
          <div className="empty-state py-12">
            <AlertCircle size={32} className="text-zinc-500 mb-2" />
            <p className="text-zinc-400 text-sm">Chưa có bài viết nào trong hàng đợi. Vui lòng chuyển sản phẩm đã SEO sang hàng đợi.</p>
          </div>
        ) : (
          <div className="table-responsive">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Product ID</th>
                  <th>Nội dung bài viết (Caption Preview)</th>
                  <th>Trạng thái</th>
                  <th>Lần thử</th>
                  <th className="actions-header">Hành động</th>
                </tr>
              </thead>
              <tbody>
                {posts.map((post) => (
                  <tr key={post.product_id}>
                    <td className="font-mono text-xs text-zinc-400">{post.product_id}</td>
                    <td>
                      <div className="text-sm max-w-md truncate text-zinc-300" title={post.caption}>
                        {post.caption}
                      </div>
                      <div className="text-xxs text-zinc-500 mt-1">
                        Hashtags: {post.hashtags.slice(0, 3).join(", ")} {post.hashtags.length > 3 ? "..." : ""}
                      </div>
                    </td>
                    <td>{getStatusBadge(post.status)}</td>
                    <td className="font-semibold text-sm text-center">{post.retry}</td>
                    <td>
                      <div className="table-actions">
                        <button
                          className="action-btn text-emerald-400 hover:bg-emerald-500/10"
                          title="Đăng bài ngay (Playwright)"
                          onClick={() => onPublish(post.product_id, fanpageUrl)}
                          disabled={isProcessing || post.status === "Publishing"}
                        >
                          <Send size={14} />
                        </button>
                        <button
                          className="action-btn text-sky-400 hover:bg-sky-500/10"
                          title="Copy Caption"
                          onClick={() => handleCopy(post.caption, post.product_id)}
                        >
                          {copiedId === post.product_id ? <CheckCircle2 size={14} className="text-emerald-400" /> : <Copy size={14} />}
                        </button>
                        <button
                          className="action-btn text-zinc-400 hover:bg-zinc-500/10"
                          title="Sửa"
                          onClick={() => openEditModal(post)}
                          disabled={isProcessing}
                        >
                          <Edit2 size={14} />
                        </button>
                        <button
                          className="action-btn text-red-400 hover:bg-red-500/10"
                          title="Xóa"
                          onClick={() => onDelete(post.product_id)}
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

      {/* Live Logger Console Card */}
      <div className="section-card input-panel-card">
        <div className="panel-header justify-between">
          <div className="flex items-center gap-2">
            <Terminal size={20} className="header-icon text-sky-400" />
            <h2>Tiến Trình Đăng Bài Live (Playwright Logs)</h2>
          </div>
          {logs.length > 0 && (
            <button className="btn-secondary py-sm px-3 text-xs flex items-center gap-1" onClick={onClearLogs}>
              <RefreshCw size={12} />
              <span>Xóa logs</span>
            </button>
          )}
        </div>

        <div className="console-body p-0 mt-3">
          {logs.length === 0 ? (
            <div className="empty-state py-8 bg-black/20 border border-zinc-800/40 rounded-lg">
              <Terminal size={24} className="text-zinc-600 mb-1" />
              <p className="text-zinc-500 text-xs font-mono">Chưa có tiến trình nào chạy. Bấm nút đăng bài để xem logs Playwright.</p>
            </div>
          ) : (
            <pre className="code-view text-xs bg-black p-4 rounded-lg overflow-y-auto max-h-64 border border-zinc-800 font-mono">
              {logs.map((logLine, idx) => (
                <div key={idx} className="mb-1 text-sky-400">
                  <span className="text-zinc-600 mr-2">[{new Date().toLocaleTimeString()}]</span>
                  {logLine}
                </div>
              ))}
            </pre>
          )}
        </div>
      </div>

      {/* Edit Queue Modal */}
      {showEditModal && editingPost && (
        <div className="modal-backdrop" onClick={() => setShowEditModal(false)}>
          <div className="modal-container max-w-lg" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Hiệu chỉnh bài viết hàng đợi</h3>
              <button className="close-btn" onClick={() => setShowEditModal(false)}>&times;</button>
            </div>
            <form onSubmit={handleSave} className="modal-form">
              <div className="form-group">
                <label className="field-label-required">Nội dung bài viết (Caption & Hashtags)</label>
                <textarea
                  value={formCaption}
                  onChange={(e) => setFormCaption(e.target.value)}
                  className="form-textarea font-sans text-sm"
                  rows={10}
                  required
                />
              </div>

              <div className="form-group">
                <label className="field-label">Trạng thái bài viết</label>
                <select
                  value={formStatus}
                  onChange={(e) => setFormStatus(e.target.value)}
                  className="form-select"
                >
                  <option value="Pending">Pending (Đang chờ đăng)</option>
                  <option value="Publishing">Publishing (Đang thực hiện đăng)</option>
                  <option value="Posted">Posted (Đã đăng bài)</option>
                  <option value="Failed">Failed (Lỗi đăng bài)</option>
                </select>
              </div>

              <div className="modal-footer">
                <button type="button" className="btn-secondary" onClick={() => setShowEditModal(false)}>Hủy</button>
                <button type="submit" className="btn-primary">Lưu bài đăng</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
