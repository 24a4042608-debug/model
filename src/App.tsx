import { useState, useEffect, useRef } from "react";
import { Sparkles, MessageSquare, RefreshCw, Store, Activity } from "lucide-react";
import { CrawlManager } from "./components/CrawlManager";
import { SeoManager } from "./components/SeoManager";
import { TelegramPanel } from "./components/TelegramPanel";
import { DecisionEngineManager } from "./components/DecisionEngineManager";

import { generateSlug } from "./utils/vietnamese";

// Types
interface RawProduct {
  id: number;
  product_id: string;
  title: string;
  description: string;
  price: number;
  price_text?: string;
  brand: string;
  category?: string;
  details_json?: string;
  images: string[];
  url: string;
  created_at?: string;
  rating_star?: number;
  sold_count?: number;
  video?: string;
}

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



// Default Seed Presets for Simulation Fallback
const DEFAULT_RAW: RawProduct[] = [
  {
    id: 1,
    product_id: "prod_byjane315",
    title: "Áo Thun Nữ Ôm Body BYJANE 315",
    description: "Chất thun tăm co giãn 4 chiều mềm mịn, thấm hút mồ hôi. Thiết kế cổ tròn, dáng ôm tôn đường cong quyến rũ. Dễ dàng mix-match với quần jean, chân váy mặc đi chơi hay đi làm đều đẹp.",
    price: 185000,
    brand: "BYJANE",
    images: ["https://images.unsplash.com/photo-1521572267360-ee0c2909d518?w=500"],
    url: "https://www.tiktok.com/@byjane/product/1783178997283"
  },
  {
    id: 2,
    product_id: "prod_ultralight",
    title: "Giày Sneaker Thể Thao Nam UltraLight",
    description: "Giày thể thao nam siêu nhẹ thế hệ mới, đế cao su êm chân chống trơn trượt hiệu quả. Vải lưới dệt kim thoáng khí không gây bí chân, thích hợp cho các hoạt động chạy bộ, gym, thể thao dã ngoại.",
    price: 480000,
    brand: "SportsPro",
    images: ["https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=500"],
    url: "https://www.tiktok.com/@sportspro/product/1783178997284"
  }
];

const DEFAULT_SEO: SeoProduct[] = [
  {
    product_id: "prod_byjane315",
    seo_title: "Áo Thun Nữ Ôm Body BYJANE 315 Co Giãn Tôn Dáng",
    meta_description: "Áo thun nữ ôm body BYJANE 315 chất thun co giãn mềm mại, tôn dáng quyến rũ, dễ phối đồ. Thiết kế basic phù hợp mặc hằng ngày cực xinh. Mua ngay hôm nay!",
    slug: "ao-thun-nu-om-body-byjane-315-co-gian-ton-dang",
    main_keyword: "áo thun nữ ôm body",
    secondary_keywords: ["áo thun nữ", "áo thun co giãn", "áo body nữ", "áo basic nữ", "BYJANE"],
    usp: ["Co giãn 4 chiều", "Mềm mịn ôm dáng", "Basic dễ phối đồ"],
    target_customer: "Nữ giới văn phòng, học sinh thích thời trang basic tôn dáng.",
    search_intent: "Tìm kiếm đồ basic tôn dáng thun thoải mái.",
    seo_score: 98,
    analysis: {
      title: "Từ khóa ở đầu tiêu đề, độ dài 49 ký tự tối ưu.",
      description: "Độ dài 149 ký tự cực chuẩn, chứa từ khóa chính và CTA kích thích mua hàng.",
      ctr: "Cao",
      suggestion: "Không cần cải thiện thêm."
    }
  }
];



export default function App() {
  const [activeTab, setActiveTab] = useState<"crawl" | "seo" | "telegram" | "decision">("crawl");
  const activeTabCrawlRequestActive = useRef(false);
  
  // Platform Lists States
  const [rawProducts, setRawProducts] = useState<RawProduct[]>([]);
  const [seoProducts, setSeoProducts] = useState<SeoProduct[]>([]);

  
  // Pipeline Progress variables
  const [isProcessing, setIsProcessing] = useState(false);
  const [activeTaskId, setActiveTaskId] = useState<string | null>(null);


  // Connection configurations
  const [isSimulation, setIsSimulation] = useState(false);
  const [apiUrl, setApiUrl] = useState("");
  const [botToken, setBotToken] = useState("");
  const [chatId, setChatId] = useState("");
  
  // Health states
  const [backendHealth, setBackendHealth] = useState<"online" | "offline" | "checking">("checking");

  // Load configuration and data on mount
  useEffect(() => {
    // Configs
    const savedSim = localStorage.getItem("auto_is_sim") === "true";
    const savedUrl = localStorage.getItem("auto_api_url") !== null ? localStorage.getItem("auto_api_url")! : "";
    const savedToken = localStorage.getItem("auto_bot_token") || "";
    const savedChatId = localStorage.getItem("auto_chat_id") || "";

    setIsSimulation(savedSim);
    setApiUrl(savedUrl);
    setBotToken(savedToken);
    setChatId(savedChatId);

    // Initial check
    checkBackendHealth(savedSim, savedUrl);
  }, []);

  // Check health and load data
  const checkBackendHealth = async (sim: boolean, url: string) => {
    // Always try to reach the backend first, regardless of sim flag
    setBackendHealth("checking");
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 3000);
      const res = await fetch(`${url}/api/system-status`, { signal: controller.signal });
      clearTimeout(timeoutId);
      if (res.ok) {
        // Backend is online — auto-switch to API mode
        setBackendHealth("online");
        setIsSimulation(false);
        localStorage.setItem("auto_is_sim", "false");
        await loadLiveBackendData(url);
        return;
      }
    } catch (err) {
      console.warn("Backend API not reachable.", err);
    }

    // Backend offline — use simulation
    setBackendHealth("offline");
    if (!sim) {
      setIsSimulation(true);
      localStorage.setItem("auto_is_sim", "true");
    }
    loadSimulatedData();
  };

  const loadSimulatedData = () => {
    const raw = localStorage.getItem("sim_raw_products");
    const seo = localStorage.getItem("sim_seo_products");

    if (raw) setRawProducts(JSON.parse(raw));
    else {
      setRawProducts(DEFAULT_RAW);
      localStorage.setItem("sim_raw_products", JSON.stringify(DEFAULT_RAW));
    }

    if (seo) setSeoProducts(JSON.parse(seo));
    else {
      setSeoProducts(DEFAULT_SEO);
      localStorage.setItem("sim_seo_products", JSON.stringify(DEFAULT_SEO));
    }
  };

  const loadLiveBackendData = async (urlHost: string) => {
    try {
      const [rawRes, seoRes, configRes] = await Promise.all([
        fetch(`${urlHost}/api/raw-products`),
        fetch(`${urlHost}/api/seo-products`),
        fetch(`${urlHost}/api/telegram-config`)
      ]);

      if (rawRes.ok) setRawProducts(await rawRes.json());
      if (seoRes.ok) setSeoProducts(await seoRes.json());
      if (configRes.ok) {
        const config = await configRes.json();
        if (config.bot_token) {
          setBotToken(config.bot_token);
          localStorage.setItem("auto_bot_token", config.bot_token);
        }
        if (config.chat_id) {
          setChatId(config.chat_id);
          localStorage.setItem("auto_chat_id", config.chat_id);
        }
      }
    } catch (e) {
      console.error("Error loading live backend datasets", e);
    }
  };

  const refreshData = async () => {
    await checkBackendHealth(isSimulation, apiUrl);
  };

  const handleSaveTelegramConfig = async (token: string, id: string) => {
    setBotToken(token);
    setChatId(id);
    localStorage.setItem("auto_bot_token", token);
    localStorage.setItem("auto_chat_id", id);
    
    if (!isSimulation) {
      try {
        const res = await fetch(`${apiUrl}/api/telegram-config`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({ bot_token: token, chat_id: id })
        });
        if (!res.ok) {
          console.error("Failed to sync Telegram config to backend");
        }
      } catch (err) {
        console.error("Error syncing Telegram config to backend:", err);
      }
    }
  };

  // ==========================================
  // CRAWL OPERATIONS
  // ==========================================

  const handleCrawl = async (url: string, method: string = "cdp", cookie: string = "") => {
    setIsProcessing(true);
    setActiveTaskId("crawl");
    
    if (isSimulation) {
      // Simulate delay
      await new Promise(r => setTimeout(r, 2000));
      // Generate simulated raw product
      const product_id = "prod_" + Math.random().toString(36).substr(2, 9);
      const isShoes = url.toLowerCase().includes("shoes") || url.toLowerCase().includes("giay");
      
      const newProd: RawProduct = {
        id: Date.now(),
        product_id,
        title: isShoes ? "Giày Sneaker Thể Thao Nam UltraLight" : "Kem Chống Nắng Vật Lý Nâng Tông SPF50+",
        description: isShoes 
          ? "Đế cao su đúc nguyên khối siêu êm và nhẹ nâng đỡ bàn chân tốt thích hợp chạy bộ và tập gym." 
          : "Bảo vệ da trước tia UVA/UVB tối ưu, kết cấu mỏng nhẹ nâng tông tự nhiên thay kem lót trang điểm.",
        price: isShoes ? 490000 : 340000,
        brand: isShoes ? "SportsPro" : "La Roche-Posay",
        images: [isShoes ? "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=500" : "https://images.unsplash.com/photo-1620916566398-39f1143ab7be?w=500"],
        url
      };

      const updated = [newProd, ...rawProducts];
      setRawProducts(updated);
      localStorage.setItem("sim_raw_products", JSON.stringify(updated));
      setIsProcessing(false);
      setActiveTaskId(null);
    } else {
      try {
        const res = await fetch(`${apiUrl}/api/crawl`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ url, method, cookie })
        });
        if (res.ok) {
          await refreshData();
        } else {
          alert("Lỗi cào sản phẩm từ API!");
        }
      } catch (err) {
        console.error(err);
      } finally {
        setIsProcessing(false);
        setActiveTaskId(null);
      }
    }
  };

  const handleCrawlShop = async (url: string, method: string = "cdp", cookie: string = "", maxProducts: number = 10) => {
    setIsProcessing(true);
    setActiveTaskId("crawl-shop");
    
    if (isSimulation) {
      // Simulate delay
      await new Promise(r => setTimeout(r, 2500));
      
      // Determine shop type and name
      let username = "byjane.hn";
      try {
        const parsed = new URL(url);
        const path = parsed.pathname.replace(/^\/|\/$/g, "");
        const parts = path.split("/").filter(p => p);
        if (parts.length > 0) {
          username = parts[0];
        }
      } catch (e) {
        username = url.split("/").pop()?.split("#")[0] || "byjane.hn";
      }

      const isByJane = username.toLowerCase().includes("jane");
      
      let newProds: RawProduct[] = [];
      if (isByJane) {
        newProds = [
          {
            id: Date.now() + 1,
            product_id: "shopee_1001",
            title: "Đầm Nữ Trễ Vai Dáng Xòe Cao Cấp ByJane",
            description: "Mẫu đầm trễ vai dáng xòe cực xinh cho các nàng diện đi chơi, đi tiệc. Chất liệu cát hàn cao cấp mềm mịn co giãn nhẹ, ôm dáng cực kỳ tôn dáng quyến rũ.",
            price: 290000,
            brand: "byjane.hn",
            images: ["https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=500"],
            url: `https://shopee.vn/product-i.320986968.1001`
          },
          {
            id: Date.now() + 2,
            product_id: "shopee_1002",
            title: "Váy Hoa Nhí Nhún Eo Vintage ByJane",
            description: "Thiết kế váy hoa nhí phong cách Hàn Quốc thanh lịch, dịu dàng. Có lót trong dày dặn, đường may tỉ mỉ, phù hợp mặc đi học, đi chơi hay đi làm.",
            price: 320000,
            brand: "byjane.hn",
            images: ["https://images.unsplash.com/photo-1612336307429-8a898d10e223?w=500"],
            url: `https://shopee.vn/product-i.320986968.1002`
          },
          {
            id: Date.now() + 3,
            product_id: "shopee_1003",
            title: "Áo Sơ Mi Nữ Tay Phồng Cổ Điển ByJane",
            description: "Áo sơ mi chất tơ gân mềm mại, dáng rộng thoải mái tay bồng cá tính. Thích hợp phối cùng chân váy hay quần tây thanh lịch.",
            price: 185000,
            brand: "byjane.hn",
            images: ["https://images.unsplash.com/photo-1548624149-f7b31668853b?w=500"],
            url: `https://shopee.vn/product-i.320986968.1003`
          },
          {
            id: Date.now() + 4,
            product_id: "shopee_1004",
            title: "Chân Váy Xếp Ly Dáng Dài Ulzzang ByJane",
            description: "Chân váy xếp ly phong cách Ulzzang basic cực kỳ dễ phối đồ. Vải tuyết mưa bền đẹp, không nhăn, có quần bảo hộ bên trong tiện lợi.",
            price: 210000,
            brand: "byjane.hn",
            images: ["https://images.unsplash.com/photo-1583496661160-fb48862c4841?w=500"],
            url: `https://shopee.vn/product-i.320986968.1004`
          },
          {
            id: Date.now() + 5,
            product_id: "shopee_1005",
            title: "Set Đầm 2 Dây Kèm Áo Khoác Cardigan ByJane",
            description: "Sét đồ thời trang năng động và gợi cảm gồm đầm thun tăm 2 dây ôm body và áo khoác mỏng nhẹ bên ngoài che khuyết điểm bắp tay hiệu quả.",
            price: 350000,
            brand: "byjane.hn",
            images: ["https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=500"],
            url: `https://shopee.vn/product-i.320986968.1005`
          },
          {
            id: Date.now() + 6,
            product_id: "shopee_1006",
            title: "Áo Kiểu Cổ Vuông Tay Lỡ Tiểu Thư ByJane",
            description: "Chất thô lụa hàn phối bèo nhẹ nhàng, tay phồng bo chun tôn ngực và eo thon gọn, mang phong cách bánh bèo dễ thương.",
            price: 195000,
            brand: "byjane.hn",
            images: ["https://images.unsplash.com/photo-1509319117193-57bab727e09d?w=500"],
            url: `https://shopee.vn/product-i.320986968.1006`
          }
        ];
      } else {
        newProds = [
          {
            id: Date.now() + 1,
            product_id: "shopee_2001",
            title: `Áo Thun Nam Nữ Unisex Store ${username}`,
            description: "Áo thun 100% cotton co giãn 4 chiều thoáng mát cực kỳ dễ phối đồ cho cả nam và nữ.",
            price: 150000,
            brand: username,
            images: ["https://images.unsplash.com/photo-1521572267360-ee0c2909d518?w=500"],
            url: `https://shopee.vn/product-i.320986968.2001`
          },
          {
            id: Date.now() + 2,
            product_id: "shopee_2002",
            title: `Giày Sneaker Thể Thao Nam Nữ Dynamic ${username}`,
            description: "Giày chạy bộ thể thao siêu nhẹ thoáng khí, đệm đế cực êm giảm chấn bảo vệ khớp gối khi vận động.",
            price: 490000,
            brand: username,
            images: ["https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=500"],
            url: `https://shopee.vn/product-i.320986968.2002`
          },
          {
            id: Date.now() + 3,
            product_id: "shopee_2003",
            title: `Balo Thời Trang Chống Nước Cao Cấp ${username}`,
            description: "Balo đựng laptop có nhiều ngăn tiện lợi làm từ vải polyester chống thấm nước, phong cách trẻ trung.",
            price: 380000,
            brand: username,
            images: ["https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=500"],
            url: `https://shopee.vn/product-i.320986968.2003`
          }
        ];
      }

      const currentIds = new Set(rawProducts.map(p => p.product_id));
      const filteredNewProds = newProds.filter(p => !currentIds.has(p.product_id));

      const updated = [...filteredNewProds, ...rawProducts];
      setRawProducts(updated);
      localStorage.setItem("sim_raw_products", JSON.stringify(updated));
      setIsProcessing(false);
      setActiveTaskId(null);
      alert(`[Simulation] Đã cào giả lập thành công ${filteredNewProds.length} sản phẩm mới từ shop ${username}!`);
    } else {
      try {
        const res = await fetch(`${apiUrl}/api/crawl-shop`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ url, method, cookie, max_products: maxProducts })
        });
        if (res.ok) {
          // Silent progress update, status will show up in the Progress Panel
          await refreshData();
        } else {
          alert("Lỗi gửi yêu cầu cào cửa hàng tới API!");
        }
      } catch (err) {
        console.error(err);
        alert("Lỗi kết nối tới server API!");
      } finally {
        setIsProcessing(false);
        setActiveTaskId(null);
      }
    }
  };

  const handleCrawlActiveTab = async () => {
    if (activeTabCrawlRequestActive.current) return;
    activeTabCrawlRequestActive.current = true;

    setIsProcessing(true);
    setActiveTaskId("crawl-active-tab");

    if (isSimulation) {
      await new Promise(r => setTimeout(r, 2000));
      alert("[Simulation] Cào từ Tab hiện tại thành công (Simulation Mode)!");
      setIsProcessing(false);
      setActiveTaskId(null);
      activeTabCrawlRequestActive.current = false;
    } else {
      try {
        const res = await fetch(`${apiUrl}/api/crawl-active-tab`, {
          method: "POST"
        });
        if (res.ok) {
          // Silent progress update, status will show up in the Progress Panel
          await refreshData();
        } else {
          // Avoid showing annoying alerts for minor 409/conflict states
          if (res.status !== 409) {
            alert("Lỗi gửi yêu cầu cào tab hiện tại tới API!");
          }
        }
      } catch (err) {
        console.error(err);
        alert("Lỗi kết nối tới server API!");
      } finally {
        setIsProcessing(false);
        setActiveTaskId(null);
        activeTabCrawlRequestActive.current = false;
      }
    }
  };


  const handleAddRaw = async (payload: any) => {
    if (isSimulation) {
      const newProd: RawProduct = {
        id: Date.now(),
        ...payload
      };
      const updated = [newProd, ...rawProducts];
      setRawProducts(updated);
      localStorage.setItem("sim_raw_products", JSON.stringify(updated));
    } else {
      await fetch(`${apiUrl}/api/raw-products`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      await refreshData();
    }
  };

  const handleUpdateRaw = async (id: number, payload: any) => {
    if (isSimulation) {
      const updated = rawProducts.map(p => p.id === id ? { ...p, ...payload } : p);
      setRawProducts(updated);
      localStorage.setItem("sim_raw_products", JSON.stringify(updated));
    } else {
      await fetch(`${apiUrl}/api/raw-products/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      await refreshData();
    }
  };

  const handleDeleteRaw = async (id: number) => {
    if (!window.confirm("Bạn có chắc chắn muốn xóa sản phẩm này khỏi kho hàng cào?")) return;
    
    if (isSimulation) {
      const updated = rawProducts.filter(p => p.id !== id);
      setRawProducts(updated);
      localStorage.setItem("sim_raw_products", JSON.stringify(updated));
    } else {
      await fetch(`${apiUrl}/api/raw-products/${id}`, { method: "DELETE" });
      await refreshData();
    }
  };

  // ==========================================
  // SEO OPERATIONS
  // ==========================================

  const handleTriggerSeo = async (productId: string) => {
    setIsProcessing(true);
    setActiveTaskId("seo");
    setActiveTab("seo");

    if (isSimulation) {
      await new Promise(r => setTimeout(r, 2000));
      const target = rawProducts.find(p => p.product_id === productId);
      if (!target) return;

      const mainKeyword = target.title.toLowerCase().includes("áo") 
        ? "áo thun nữ ôm body" 
        : (target.title.toLowerCase().includes("giày") ? "giày thể thao nam" : target.title.toLowerCase().slice(0, 20));
      
      const newSeo: SeoProduct = {
        product_id: productId,
        seo_title: `${mainKeyword.toUpperCase()} - ${target.brand} Cao Cấp Co Giãn Cực Đẹp`,
        meta_description: `${target.title} chất liệu cao cấp bền đẹp, thấm hút mồ hôi tốt mang lại sự thoải mái nhất. Mua ngay hôm nay để nhận ưu đãi!`,
        slug: generateSlug(target.title),
        main_keyword: mainKeyword,
        secondary_keywords: [mainKeyword, "sản phẩm hot", target.brand],
        usp: ["Thấm hút mồ hôi tốt", "Thiết kế trẻ trung"],
        target_customer: "Người tiêu dùng mua sắm trực tuyến",
        search_intent: "Mua hàng thời trang thể thao",
        seo_score: 95,
        analysis: {
          title: "Đạt chuẩn độ dài, từ khóa chính ở đầu.",
          description: "Độ dài đạt chuẩn, đầy đủ CTA.",
          ctr: "Cao",
          suggestion: "Tốt, không cần sửa đổi thêm."
        }
      };

      const updated = [newSeo, ...seoProducts.filter(s => s.product_id !== productId)];
      setSeoProducts(updated);
      localStorage.setItem("sim_seo_products", JSON.stringify(updated));
      setIsProcessing(false);
      setActiveTaskId(null);
    } else {
      try {
        const res = await fetch(`${apiUrl}/api/seo-products/${productId}`, { method: "POST" });
        if (res.ok) {
          await refreshData();
        } else {
          alert("Lỗi tối ưu SEO sản phẩm từ API!");
        }
      } catch (err) {
        console.error(err);
      } finally {
        setIsProcessing(false);
        setActiveTaskId(null);
      }
    }
  };

  const handleUpdateSeo = async (productId: string, payload: any) => {
    if (isSimulation) {
      const updated = seoProducts.map(s => s.product_id === productId ? { ...s, ...payload } : s);
      setSeoProducts(updated);
      localStorage.setItem("sim_seo_products", JSON.stringify(updated));
    } else {
      await fetch(`${apiUrl}/api/seo-products/${productId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      await refreshData();
    }
  };

  const handleDeleteSeo = async (productId: string) => {
    if (!window.confirm("Bạn có chắc chắn muốn xóa bản SEO này?")) return;
    
    if (isSimulation) {
      const updated = seoProducts.filter(s => s.product_id !== productId);
      setSeoProducts(updated);
      localStorage.setItem("sim_seo_products", JSON.stringify(updated));
    } else {
      await fetch(`${apiUrl}/api/seo-products/${productId}`, { method: "DELETE" });
      await refreshData();
    }
  };



  const handleSendTestTelegram = async (message: string) => {
    // Send a test message via Telegram
    if (isSimulation) {
      alert(`[Simulation] Đã gửi thông báo test: "${message}"`);
    } else {
      try {
        const botUrl = `https://api.telegram.org/bot${botToken}/sendMessage`;
        const res = await fetch(botUrl, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            chat_id: chatId,
            text: message
          })
        });
        if (res.ok) {
          alert("Đã gửi tin nhắn test thành công! Hãy kiểm tra ứng dụng Telegram của bạn.");
        } else {
          const errData = await res.json();
          alert(`Lỗi Telegram API: ${errData.description || "Không xác định"}`);
        }
      } catch (err: any) {
        alert(`Lỗi kết nối mạng khi gửi test Telegram: ${err.message}`);
      }
    }
  };

  return (
    <div className="app-container">
      {/* Left Sidebar Navigation */}
      <aside className="dashboard-sidebar">
        <div className="flex flex-col gap-6">
          {/* Brand header */}
          <div className="flex items-center gap-3 px-1 py-1">
            <div className="logo-icon-glow">
              <Sparkles size={20} className="icon-glow" />
            </div>
            <div>
              <h1 className="text-sm font-bold tracking-tight bg-gradient-to-r from-white to-violet-400 bg-clip-text text-transparent" style={{ fontSize: "1.1rem", margin: 0 }}>E-Commerce AI</h1>
              <p className="text-[10px] text-zinc-500" style={{ margin: 0 }}>Automation Platform</p>
            </div>
          </div>

          {/* Navigation Menu links */}
          <nav className="sidebar-nav">
            <button 
              className={`sidebar-btn ${activeTab === "crawl" ? "active" : ""}`}
              onClick={() => setActiveTab("crawl")}
            >
              <Store size={16} />
              <span>1. Sản phẩm</span>
            </button>
            <button 
              className={`sidebar-btn ${activeTab === "seo" ? "active" : ""}`}
              onClick={() => setActiveTab("seo")}
            >
              <Sparkles size={16} />
              <span>2. Tối ưu SEO</span>
            </button>
            <button 
              className={`sidebar-btn ${activeTab === "telegram" ? "active" : ""}`}
              onClick={() => setActiveTab("telegram")}
            >
              <MessageSquare size={16} />
              <span>3. Cài đặt & Bot</span>
            </button>
            <button 
              className={`sidebar-btn ${activeTab === "decision" ? "active" : ""}`}
              onClick={() => setActiveTab("decision")}
            >
              <Activity size={16} />
              <span>4. Tối ưu ROAS</span>
            </button>
          </nav>
        </div>

        {/* Sidebar Footer Status */}
        <div className="flex flex-col gap-2 border-t border-zinc-800/60 pt-4 text-center">
          <span className={`px-2 py-1 rounded-md text-[10px] font-bold uppercase tracking-wider border ${
            backendHealth === "online" 
              ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" 
              : (backendHealth === "checking" ? "bg-zinc-500/10 text-zinc-400 border-zinc-500/20" : "bg-amber-500/10 text-amber-400 border-amber-500/20")
          }`}>
            {backendHealth === "online" ? "API Live" : (backendHealth === "checking" ? "Đang kết nối..." : "Simulation")}
          </span>
          <p className="text-[10px] text-zinc-600 mt-1">Version 1.2.0</p>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="main-content-wrapper">
        {/* Topbar Header */}
        <header className="dashboard-topbar">
          <h2 className="text-xs font-bold text-zinc-200 uppercase tracking-wider" style={{ margin: 0 }}>
            {activeTab === "crawl" && "1. Quản lý kho hàng & catalog"}
            {activeTab === "seo" && "2. Tối ưu hóa SEO bằng Trí tuệ Nhân tạo"}
            {activeTab === "telegram" && "3. Cấu hình Tham số hệ thống & Bot thông báo"}
            {activeTab === "decision" && "4. Dự báo mô phỏng & Đề xuất ROAS thầu"}
          </h2>

          <div className="flex items-center gap-2">
            <button className="btn-secondary py-1 px-3 text-xs flex items-center gap-1.5 border border-zinc-850 hover:bg-zinc-800" onClick={refreshData}>
              <RefreshCw size={12} className={isProcessing ? "animate-spin" : ""} />
              <span>Đồng bộ dữ liệu</span>
            </button>
          </div>
        </header>

        {/* Main Content Body */}
        <main className="dashboard-results-area p-6 flex-1">
          {activeTab === "crawl" && (
            <CrawlManager
              products={rawProducts}
              onAdd={handleAddRaw}
              onUpdate={handleUpdateRaw}
              onDelete={handleDeleteRaw}
              onCrawl={handleCrawl}
              onCrawlShop={handleCrawlShop}
              onCrawlActiveTab={handleCrawlActiveTab}
              onTriggerSeo={handleTriggerSeo}
              isProcessing={isProcessing}
              activeTaskId={activeTaskId}
              apiUrl={apiUrl}
              isSimulation={isSimulation}
              onRefreshData={refreshData}
            />
          )}

          {activeTab === "seo" && (
            <SeoManager
              products={seoProducts}
              onUpdate={handleUpdateSeo}
              onDelete={handleDeleteSeo}
              isProcessing={isProcessing}
            />
          )}

          {activeTab === "telegram" && (
            <div className="flex flex-col gap-6">
              <TelegramPanel
                apiUrl={apiUrl}
                onChangeApiUrl={(url) => {
                  setApiUrl(url);
                  localStorage.setItem("auto_api_url", url);
                  checkBackendHealth(isSimulation, url);
                }}
                botToken={botToken}
                chatId={chatId}
                onChangeToken={(token) => handleSaveTelegramConfig(token, chatId)}
                onChangeChatId={(id) => handleSaveTelegramConfig(botToken, id)}
                onSendTestAlert={handleSendTestTelegram}
                isProcessing={isProcessing}
              />
            </div>
          )}

          {activeTab === "decision" && (
            <DecisionEngineManager
              apiUrl={apiUrl}
              isSimulation={isSimulation}
            />
          )}
        </main>

        <footer className="app-footer mt-12 pb-4 px-6">
          <p>© 2026 E-Commerce Automation Platform - Đóng gói bằng Playwright, FastAPI, MySQL XAMPP và Google Gemini API.</p>
        </footer>
      </div>
    </div>
  );
}
