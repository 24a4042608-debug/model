import React, { useState, useEffect } from "react";
import { Send, MessageSquare, ShieldCheck, Play, HelpCircle, Globe } from "lucide-react";

interface TelegramPanelProps {
  apiUrl: string;
  onChangeApiUrl: (url: string) => void;
  botToken: string;
  chatId: string;
  onChangeToken: (token: string) => void;
  onChangeChatId: (id: string) => void;
  onSendTestAlert: (message: string) => Promise<void>;
  isProcessing: boolean;
}

export const TelegramPanel: React.FC<TelegramPanelProps> = ({
  apiUrl,
  onChangeApiUrl,
  botToken,
  chatId,
  onChangeToken,
  onChangeChatId,
  onSendTestAlert,
  isProcessing
}) => {
  const [testMsg, setTestMsg] = useState("🔔 Cảnh báo: Kết nối thành công từ E-Commerce SEO Automation Dashboard!");
  const [tokenInput, setTokenInput] = useState(botToken);
  const [chatIdInput, setChatIdInput] = useState(chatId);
  const [apiInput, setApiInput] = useState(apiUrl);
  const [showToken, setShowToken] = useState(false);
  const [showSetupGuide, setShowSetupGuide] = useState(false);

  // Keep local apiInput state in sync when parent prop changes
  useEffect(() => {
    setApiInput(apiUrl);
  }, [apiUrl]);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    onChangeToken(tokenInput);
    onChangeChatId(chatIdInput);
    alert("Đã lưu cấu hình kết nối Telegram! Hãy kiểm tra bằng cách bấm nút Gửi tin nhắn test.");
  };

  const handleTest = async () => {
    if (!tokenInput || !chatIdInput) {
      alert("Vui lòng điền đủ Bot Token và Chat ID trước khi test!");
      return;
    }
    await onSendTestAlert(testMsg);
  };

  const commands = [
    { cmd: "/status", desc: "Xem nhanh số lượng sản phẩm cào, SEO và hàng đợi Facebook" },
    { cmd: "/search <Từ khóa>", desc: "Tìm nhanh mã sản phẩm (Product ID) trong hệ thống bằng tên hoặc ID" },
    { cmd: "/products", desc: "Xem danh sách 10 sản phẩm vừa mới cào gần đây nhất" },
    { cmd: "/top", desc: "Xem bảng vàng sản phẩm nổi bật (bán chạy nhất & đánh giá cao nhất)" },
    { cmd: "/bestselling", desc: "Xem danh sách 10 sản phẩm bán chạy nhất trong hệ thống" },
    { cmd: "/toprate", desc: "Xem danh sách 10 sản phẩm được đánh giá tốt nhất từ khách hàng" },
    { cmd: "/crawl <URL>", desc: "Cào sản phẩm từ Link Shop Shopee (chạy CDP Chrome 9222)" },
    { cmd: "/crawltab", desc: "Cào nhanh sản phẩm từ Tab Shopee đang hoạt động trên Chrome chính" },
    { cmd: "/seo <ID>", desc: "Chạy tối ưu SEO bằng AI Gemini (sửa tiêu đề, từ khóa, viết mô tả và USP)" },
    { cmd: "/fb <ID>", desc: "Tạo nội dung bài viết cho Facebook Fanpage và lưu vào hàng đợi" },
    { cmd: "/publish", desc: "Đăng bài viết tiếp theo có trạng thái Pending trong hàng đợi lên Facebook" }
  ];

  return (
    <div className="manager-section grid grid-cols-1 md:grid-cols-2 gap-6">
      <div className="flex flex-col gap-6">
        {/* API Connection Card */}
        <div className="section-card input-panel-card">
          <div className="panel-header">
            <Globe size={20} className="header-icon text-emerald-400" />
            <h2>Cấu hình Kết nối API Backend</h2>
          </div>
          <p className="setting-desc -mt-2">
            Định cấu hình địa chỉ máy chủ API (FastAPI) để đồng bộ dữ liệu. Mặc định là chuỗi trống (Tự động nhận dạng tương đối) giúp chạy qua ngrok tiện lợi nhất.
          </p>

          <form onSubmit={(e) => {
            e.preventDefault();
            onChangeApiUrl(apiInput);
            alert("Đã cập nhật địa chỉ API Backend! Hệ thống đang thử kết nối lại...");
          }} className="product-form mt-2">
            <div className="form-group">
              <label className="field-label">API Server URL</label>
              <input
                type="text"
                value={apiInput}
                onChange={(e) => setApiInput(e.target.value)}
                placeholder="Ví dụ: http://localhost:8000 hoặc để trống"
                className="form-input"
              />
              <p className="setting-desc mt-1">
                Trạng thái: <strong>{apiUrl ? `Cấu hình thủ công (${apiUrl})` : "Tự động phát hiện (Proxy tương đối)"}</strong>
              </p>
            </div>

            <div className="flex gap-2">
              <button type="submit" className="btn-secondary flex-1 justify-center">
                <ShieldCheck size={16} />
                <span>Lưu địa chỉ API</span>
              </button>
              <button 
                type="button" 
                onClick={() => {
                  setApiInput("");
                  onChangeApiUrl("");
                  alert("Đã chuyển về chế độ Tự động phát hiện (Proxy tương đối)!");
                }} 
                className="btn-secondary px-3"
                title="Khôi phục mặc định"
              >
                Reset
              </button>
            </div>
          </form>
        </div>

        {/* Configuration Card */}
        <div className="section-card input-panel-card">
          <div className="panel-header">
            <MessageSquare size={20} className="header-icon text-violet" />
            <h2>Cấu hình Telegram Bot</h2>
          </div>
          <p className="setting-desc -mt-2">
            Kết nối Telegram giúp bạn ra lệnh cào, SEO, đăng bài tự động từ xa mà không cần mở giao diện Web.
          </p>

          {/* Collapsible Setup Guide */}
          <div className="bg-violet-glow border-violet-glow rounded-lg p-3 my-3">
            <button 
              type="button"
              onClick={() => setShowSetupGuide(!showSetupGuide)}
              className="flex items-center justify-between w-full text-xs font-semibold text-violet"
            >
              <span className="flex items-center gap-1.5">
                <HelpCircle size={14} className="text-violet" />
                Hướng dẫn liên kết Telegram Bot (3 bước đơn giản)
              </span>
              <span>{showSetupGuide ? "▲ Thu gọn" : "▼ Mở rộng"}</span>
            </button>
            {showSetupGuide && (
              <div className="mt-2.5 text-xs text-zinc-500 flex flex-col gap-2.5 border-t pt-2.5">
                <div>
                  <strong className="text-violet block mb-0.5">Bước 1: Tạo Bot Telegram mới</strong>
                  <p className="text-zinc-500 pl-3.5 leading-relaxed">
                    Truy cập <a href="https://t.me/BotFather" target="_blank" rel="noreferrer" className="text-sky underline hover:text-sky">@BotFather</a> trên Telegram, gõ <code className="bg-black/20 px-1 rounded text-violet font-semibold">/newbot</code> và làm theo hướng dẫn để đặt tên bot. Bạn sẽ nhận được một chuỗi <strong className="text-primary font-bold">Token</strong> (ví dụ: <code className="bg-black/20 px-1 rounded text-violet font-mono text-[10px]">12345678:AA...</code>). Hãy dán Token đó vào ô cấu hình bên dưới.
                  </p>
                </div>
                <div>
                  <strong className="text-violet block mb-0.5">Bước 2: Lấy Chat ID của bạn</strong>
                  <p className="text-zinc-500 pl-3.5 leading-relaxed">
                    - <strong>Nhận thông báo cá nhân:</strong> Tìm bot <a href="https://t.me/userinfobot" target="_blank" rel="noreferrer" className="text-sky underline hover:text-sky">@userinfobot</a> hoặc <a href="https://t.me/raw_data_bot" target="_blank" rel="noreferrer" className="text-sky underline hover:text-sky">@raw_data_bot</a>, bấm <strong className="text-violet font-bold">Start</strong> để nhận chuỗi ID số (ví dụ: <code className="text-zinc-500 bg-black/20 px-1 rounded font-mono font-semibold">987654321</code>).<br />
                    - <strong>Nhận thông báo nhóm:</strong> Thêm bot của bạn vào nhóm làm Quản trị viên, gửi một tin nhắn bất kỳ vào nhóm đó. Sau đó mở trình duyệt truy cập link: <code className="text-zinc-500 bg-black/20 px-1 rounded break-all font-mono text-[10px]">https://api.telegram.org/bot[TOKEN_CỦA_BẠN]/getUpdates</code> và tìm phần <code className="text-violet font-semibold">{"\"chat\":{\"id\":-...}"}</code> (ID nhóm sẽ có dấu trừ đằng trước).
                  </p>
                </div>
                <div>
                  <strong className="text-violet block mb-0.5">Bước 3: Khởi động Bot & Lưu cấu hình</strong>
                  <p className="text-zinc-500 pl-3.5 leading-relaxed">
                    Tìm bot của chính bạn trên Telegram và bấm nút <strong className="text-violet font-bold">Start</strong> (hoặc gõ <code className="bg-black/20 px-1 rounded text-violet font-semibold">/start</code>) để bắt đầu. Tiếp theo, điền đủ thông tin Token và Chat ID vào form, bấm <strong className="text-violet font-bold">Lưu kết nối</strong>. Sau đó thử nhập nội dung tin nhắn kiểm tra ở dưới rồi ấn <strong className="text-violet font-bold">Gửi Test</strong>.
                  </p>
                </div>
              </div>
            )}
          </div>

          <form onSubmit={handleSave} className="product-form mt-2">
            <div className="form-group">
              <label className="field-label">Telegram Bot Token</label>
              <div className="password-input-wrapper">
                <input
                  type={showToken ? "text" : "password"}
                  value={tokenInput}
                  onChange={(e) => setTokenInput(e.target.value)}
                  placeholder="Ví dụ: 1234567890:ABCdefGhI..."
                  className="form-input w-full pr-10"
                />
                <button 
                  type="button" 
                  onClick={() => setShowToken(!showToken)}
                  className="password-toggle"
                >
                  {showToken ? "Ẩn" : "Hiện"}
                </button>
              </div>
            </div>

            <div className="form-group">
              <label className="field-label">Telegram Chat ID (ID người nhận/nhóm)</label>
              <input
                type="text"
                value={chatIdInput}
                onChange={(e) => setChatIdInput(e.target.value)}
                placeholder="Ví dụ: 987654321 hoặc -100123456789"
                className="form-input"
              />
              <p className="setting-desc">
                Nhắn tin cho bot <a href="https://t.me/userinfobot" target="_blank" rel="noreferrer">@userinfobot</a> hoặc <a href="https://t.me/raw_data_bot" target="_blank" rel="noreferrer">@raw_data_bot</a> để lấy Chat ID cá nhân của bạn.
              </p>
            </div>

            <button type="submit" className="btn-secondary w-full justify-center">
              <ShieldCheck size={16} />
              <span>Lưu kết nối</span>
            </button>
          </form>

          <div className="border-t border-zinc-800/60 pt-4 mt-2">
            <label className="field-label mb-2 block">Gửi thông báo Test</label>
            <div className="flex gap-2">
              <input
                type="text"
                value={testMsg}
                onChange={(e) => setTestMsg(e.target.value)}
                className="form-input flex-1 text-xs"
              />
              <button
                onClick={handleTest}
                className="btn-primary px-4 py-2 text-xs"
                disabled={isProcessing}
              >
                <Send size={12} />
                <span>Gửi Test</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Guide Command Card */}
      <div className="section-card input-panel-card">
        <div className="panel-header">
          <HelpCircle size={20} className="header-icon text-sky" />
          <h2>Hướng dẫn Câu lệnh Telegram Bot</h2>
        </div>
        <p className="setting-desc -mt-2">
          Sau khi lưu cấu hình, bạn có thể mở ứng dụng Telegram và nhắn tin trực tiếp các câu lệnh sau cho Bot:
        </p>

        <div className="flex flex-col gap-3 mt-2">
          {commands.map((c, i) => (
            <div key={i} className="bg-sky-glow border border-sky-glow p-3 rounded-lg flex flex-col gap-1">
              <div className="flex items-center gap-2">
                <Play size={10} className="text-sky" />
                <span className="font-mono text-sm text-sky font-bold">{c.cmd}</span>
              </div>
              <span className="text-xs text-zinc-500 pl-4">{c.desc}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
