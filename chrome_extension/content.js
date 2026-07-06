// Content script for Shopee Automation Grabber
(function() {
  console.log("🔌 [Shopee Automation Grabber] Content script loaded.");

  // Default API URL
  let apiHost = "http://localhost:8000";

  // Load saved API URL from extension storage if available
  if (typeof chrome !== 'undefined' && chrome.storage && chrome.storage.local) {
    chrome.storage.local.get(['apiUrl'], function(result) {
      if (result.apiUrl) {
        apiHost = result.apiUrl;
      }
    });
  }

  // Create & Inject floating UI HUD
  let hud = null;
  function initHUD() {
    if (document.getElementById('shopee-scraper-hud')) return;

    hud = document.createElement('div');
    hud.id = 'shopee-scraper-hud';
    hud.style.cssText = `
      position: fixed;
      bottom: 20px;
      right: 20px;
      width: 320px;
      background: rgba(18, 18, 24, 0.85);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 12px;
      padding: 16px;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
      z-index: 999999;
      font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      color: #e4e4e7;
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    `;

    hud.innerHTML = `
      <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
        <div style="display: flex; align-items: center; gap: 8px;">
          <div style="width: 8px; height: 8px; border-radius: 50%; background: #a78bfa; box-shadow: 0 0 8px #a78bfa;" id="hud-pulse"></div>
          <span style="font-weight: 700; font-size: 13px; letter-spacing: 0.5px; color: #f4f4f5; text-transform: uppercase;">Shopee Grabber 🔌</span>
        </div>
        <button id="hud-close-btn" style="background: none; border: none; color: #a1a1aa; cursor: pointer; font-size: 16px; padding: 0 4px; line-height: 1;">&times;</button>
      </div>
      <div id="hud-body" style="font-size: 12px; line-height: 1.5; color: #a1a1aa;">
        Đang khởi tạo...
      </div>
      <div id="hud-actions" style="margin-top: 12px; display: flex; gap: 8px;"></div>
    `;

    document.body.appendChild(hud);

    document.getElementById('hud-close-btn').addEventListener('click', () => {
      hud.style.opacity = '0';
      hud.style.transform = 'translateY(20px)';
      setTimeout(() => {
        if (hud) hud.remove();
      }, 300);
    });
  }

  function updateHUD(statusHtml, pulseColor = "#a78bfa") {
    initHUD();
    const body = document.getElementById('hud-body');
    const pulse = document.getElementById('hud-pulse');
    if (body) body.innerHTML = statusHtml;
    if (pulse) {
      pulse.style.background = pulseColor;
      pulse.style.boxShadow = `0 0 8px ${pulseColor}`;
    }
  }

  function addHUDAction(label, onClick, isPrimary = false) {
    initHUD();
    const actionsContainer = document.getElementById('hud-actions');
    if (!actionsContainer) return;

    const btn = document.createElement('button');
    btn.innerText = label;
    btn.style.cssText = isPrimary ? `
      flex: 1;
      background: linear-gradient(135deg, #8b5cf6, #ec4899);
      border: none;
      color: #fff;
      padding: 8px 12px;
      border-radius: 6px;
      font-weight: 600;
      font-size: 11px;
      cursor: pointer;
      box-shadow: 0 2px 8px rgba(139, 92, 246, 0.3);
      transition: all 0.2s;
    ` : `
      flex: 1;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.1);
      color: #e4e4e7;
      padding: 8px 12px;
      border-radius: 6px;
      font-weight: 500;
      font-size: 11px;
      cursor: pointer;
      transition: all 0.2s;
    `;

    btn.addEventListener('mouseenter', () => {
      btn.style.filter = 'brightness(1.1)';
    });
    btn.addEventListener('mouseleave', () => {
      btn.style.filter = 'none';
    });

    btn.addEventListener('click', onClick);
    actionsContainer.appendChild(btn);
  }

  function clearHUDActions() {
    const actionsContainer = document.getElementById('hud-actions');
    if (actionsContainer) actionsContainer.innerHTML = '';
  }

  // Parse product details from page
  function scrapeProductDetails() {
    let result = {
      product_id: "",
      title: "",
      description: "",
      price: 0.0,
      price_text: "",
      brand: "Shopee Acc",
      category: "Shopee",
      details_json: "{}",
      images: [],
      video: "",
      url: window.location.href,
      rating_star: null,
      sold_count: null
    };

    // 1. Title
    const h1 = document.querySelector('h1') || document.querySelector('h1.vR6K3w');
    if (h1) {
      result.title = h1.innerText.trim();
    }

    // 2. Price
    const priceEl = document.querySelector('div.pmmxKx') || document.querySelector('div.G27FPf') || document.querySelector('.F3493d');
    if (priceEl) {
      result.price_text = priceEl.innerText.trim();
      const cleanNum = result.price_text.replace(/[^\d]/g, '');
      if (cleanNum) {
        result.price = parseFloat(cleanNum);
      }
    }

    // 3. Category & Details specifications
    const specs = {};
    const rows = document.querySelectorAll('div.ybxj32');
    rows.forEach(row => {
      const label = row.querySelector('h3') || row.querySelector('label');
      if (label) {
        const key = label.innerText.trim();
        let val = "";
        
        if (key.includes("Danh Mục") || key.toLowerCase().includes("category")) {
          const links = row.querySelectorAll('a');
          const cats = [];
          links.forEach(a => {
            if (a.innerText.trim() && a.innerText.trim() !== "Shopee") {
              cats.push(a.innerText.trim());
            }
          });
          val = cats.join(" > ");
          result.category = val;
        } else {
          // Find siblings or non-label text
          const children = Array.from(row.children);
          const valEl = children.find(c => c !== label);
          if (valEl) {
            val = valEl.innerText.trim();
          }
        }
        
        if (key && val) {
          specs[key] = val;
        }
      }
    });
    result.details_json = JSON.stringify(specs);
    if (specs["Thương hiệu"]) {
      result.brand = specs["Thương hiệu"];
    }

    // 4. Description
    const descSection = Array.from(document.querySelectorAll('section')).find(s => {
      const h2 = s.querySelector('h2');
      return h2 && (h2.innerText.toUpperCase().includes("MÔ TẢ") || h2.innerText.toUpperCase().includes("DESCRIPTION"));
    });
    if (descSection) {
      const descDiv = descSection.querySelector('div.Gf4Ro0') || descSection.querySelector('div.e8lZp3') || descSection.querySelector('p');
      if (descDiv) {
        result.description = descDiv.innerText.trim();
      }
    }

    // 5. Images
    const imageSet = new Set();
    const imgs = document.querySelectorAll('img');
    imgs.forEach(img => {
      const src = img.src || "";
      if (src.includes("susercontent.com") && !src.includes("resize")) {
        // Clean thumb suffix
        const clean = src.split('_tn')[0].split('_tn')[0];
        imageSet.add(clean);
      }
    });
    result.images = Array.from(imageSet).slice(0, 10);

    // 6. Rating & Sold
    const ratingEl = document.querySelector('.F9uo3e');
    if (ratingEl) {
      const r = parseFloat(ratingEl.innerText.trim());
      if (r >= 1 && r <= 5) result.rating_star = r;
    }

    // Parse sold count
    const texts = Array.from(document.querySelectorAll('div, span')).map(el => el.innerText || "");
    for (const text of texts) {
      if (text.toLowerCase().includes("đã bán") || text.toLowerCase().includes("sold")) {
        const match = text.match(/([\d\.,]+)\s*([kK]?)/);
        if (match) {
          let val = parseFloat(match[1].replace(',', '.'));
          if (match[2].toLowerCase() === 'k') {
            val *= 1000;
          }
          result.sold_count = Math.round(val);
          break;
        }
      }
    }

    // 7. Product ID from URL
    const url = window.location.href;
    const match = url.match(/[iI]\.(\d+)\.(\d+)/) || url.match(/\/product\/(\d+)\/(\d+)/);
    if (match) {
      result.product_id = `${match[1]}_${match[2]}`;
    } else {
      result.product_id = "ext_" + Math.random().toString(36).substring(2, 11);
    }

    // 8. Try JSON-LD schema fallback
    let jsonLdProduct = null;
    const scripts = document.querySelectorAll('script[type="application/ld+json"]');
    scripts.forEach(script => {
      try {
        const data = JSON.parse(script.textContent);
        if (Array.isArray(data)) {
          const found = data.find(item => item['@type'] === 'Product');
          if (found) jsonLdProduct = found;
        } else if (data['@type'] === 'Product') {
          jsonLdProduct = data;
        } else if (data['@graph']) {
          const found = data['@graph'].find(item => item['@type'] === 'Product');
          if (found) jsonLdProduct = found;
        }
      } catch (e) {}
    });

    if (jsonLdProduct) {
      console.log("🎯 Found JSON-LD Schema: ", jsonLdProduct);
      if (!result.title && jsonLdProduct.name) result.title = jsonLdProduct.name;
      if (!result.description && jsonLdProduct.description) result.description = jsonLdProduct.description;
      if (jsonLdProduct.image && result.images.length === 0) {
        result.images = Array.isArray(jsonLdProduct.image) ? jsonLdProduct.image : [jsonLdProduct.image];
      }
      if (jsonLdProduct.offers) {
        const offers = jsonLdProduct.offers;
        const p = offers.lowPrice || offers.price;
        if (p && result.price === 0) {
          result.price = parseFloat(p);
          result.price_text = `₫${result.price.toLocaleString('vi-VN')}`;
        }
      }
      if (jsonLdProduct.aggregateRating && result.rating_star === null) {
        const r = parseFloat(jsonLdProduct.aggregateRating.ratingValue);
        if (r >= 1 && r <= 5) result.rating_star = r;
      }
    }

    return result;
  }

  // Send product data to local backend
  function sendProductToBackend(product) {
    updateHUD(`
      <div style="font-weight: 600; color: #f4f4f5; margin-bottom: 4px;">Đang gửi dữ liệu...</div>
      <div style="color: #a78bfa; font-weight: 500;">${product.title ? product.title.substring(0, 50) + "..." : "Sản phẩm Shopee"}</div>
      <div style="margin-top: 4px; font-size: 10px;">Backend: ${apiHost}</div>
    `, "#f59e0b");

    fetch(`${apiHost}/api/extension/crawl`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(product)
    })
    .then(response => {
      if (!response.ok) throw new Error("API response error");
      return response.json();
    })
    .then(data => {
      console.log("✅ [Shopee Scraper] Data sent successfully:", data);
      updateHUD(`
        <div style="font-weight: 600; color: #34d399; margin-bottom: 4px;">✅ Đã đồng bộ thành công!</div>
        <div style="color: #e4e4e7;">Sản phẩm đã được lưu vào database và đồng bộ lên Telegram.</div>
        <div style="margin-top: 6px; font-size: 10px; color: #a1a1aa;">ID: ${product.product_id}</div>
      `, "#10b981");

      clearHUDActions();
      addHUDAction("⚡ Gửi lại dữ liệu", () => {
        sendProductToBackend(product);
      });
    })
    .catch(error => {
      console.error("❌ [Shopee Scraper] Fetch error:", error);
      updateHUD(`
        <div style="font-weight: 600; color: #f87171; margin-bottom: 4px;">❌ Lỗi kết nối Backend</div>
        <div style="color: #e4e4e7;">Không thể kết nối đến Backend tại <code>${apiHost}</code>.</div>
        <div style="margin-top: 4px; font-size: 10px;">Vui lòng kiểm tra xem Backend API Server đã khởi chạy hay chưa.</div>
      `, "#ef4444");

      clearHUDActions();
      addHUDAction("🔄 Thử lại", () => {
        sendProductToBackend(product);
      }, true);
    });
  }

  // Scan product links on a Shop page
  function scanShopProducts() {
    updateHUD(`
      <div style="font-weight: 600; color: #f4f4f5; margin-bottom: 4px;">Đang quét trang cửa hàng...</div>
      <div>Vui lòng đợi cuộn trang để tìm kiếm sản phẩm.</div>
    `, "#f59e0b");

    // Scroll down and up to trigger Shopee lazy-loading
    let totalScrolls = 5;
    let currentScroll = 0;
    
    const interval = setInterval(() => {
      window.scrollTo(0, (currentScroll + 1) * 800);
      currentScroll++;
      
      updateHUD(`
        <div style="font-weight: 600; color: #f4f4f5; margin-bottom: 4px;">Đang quét trang cửa hàng...</div>
        <div>Cuộn trang: ${currentScroll}/${totalScrolls} để tìm sản phẩm</div>
      `, "#f59e0b");

      if (currentScroll >= totalScrolls) {
        clearInterval(interval);
        window.scrollTo(0, 0);
        
        // Extract product links
        const anchors = document.querySelectorAll('a');
        const urls = [];
        anchors.forEach(a => {
          const href = a.href || "";
          if (href && (href.includes("-i.") || href.includes("/product/"))) {
            const clean = href.split('?')[0].split('#')[0];
            if (!urls.includes(clean)) {
              urls.push(clean);
            }
          }
        });

        console.log(`🔍 [Shopee Grabber] Found ${urls.length} product links.`);

        if (urls.length === 0) {
          updateHUD(`
            <div style="font-weight: 600; color: #f87171; margin-bottom: 4px;">⚠️ Không tìm thấy sản phẩm nào</div>
            <div style="color: #e4e4e7;">Hãy thử cuộn trang xuống sâu hơn hoặc kiểm tra xem trang có sản phẩm hiển thị không.</div>
          `, "#f59e0b");
          clearHUDActions();
          addHUDAction("⚡ Quét lại", scanShopProducts, true);
        } else {
          updateHUD(`
            <div style="font-weight: 600; color: #34d399; margin-bottom: 4px;">🔍 Đã quét xong!</div>
            <div style="color: #e4e4e7;">Tìm thấy <strong>${urls.length}</strong> sản phẩm hợp lệ trên trang.</div>
          `, "#10b981");

          clearHUDActions();
          addHUDAction("⚡ Gửi ${urls.length} links về Backend", () => {
            sendShopUrlsToBackend(urls);
          }, true);
        }
      }
    }, 1000);
  }

  // Send list of product URLs to backend
  function sendShopUrlsToBackend(urls) {
    updateHUD(`
      <div style="font-weight: 600; color: #f4f4f5; margin-bottom: 4px;">Đang đồng bộ danh sách sản phẩm...</div>
      <div>Đang gửi ${urls.length} sản phẩm về backend để cào.</div>
    `, "#f59e0b");

    fetch(`${apiHost}/api/extension/crawl-shop`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        shop_url: window.location.href,
        urls: urls
      })
    })
    .then(response => {
      if (!response.ok) throw new Error("API response error");
      return response.json();
    })
    .then(data => {
      updateHUD(`
        <div style="font-weight: 600; color: #34d399; margin-bottom: 4px;">✅ Đã gửi danh sách thành công!</div>
        <div style="color: #e4e4e7;">Backend đang cào <strong>${urls.length}</strong> sản phẩm trong background.</div>
      `, "#10b981");
      clearHUDActions();
    })
    .catch(error => {
      updateHUD(`
        <div style="font-weight: 600; color: #f87171; margin-bottom: 4px;">❌ Lỗi kết nối Backend</div>
        <div style="color: #e4e4e7;">Không thể gửi danh sách đến Backend tại <code>${apiHost}</code>.</div>
      `, "#ef4444");
      clearHUDActions();
      addHUDAction("🔄 Thử lại", () => sendShopUrlsToBackend(urls), true);
    });
  }

  // Route URL on load
  function executeGrabber() {
    const url = window.location.href;
    const isProductPage = url.includes("-i.") || url.includes("/product/");
    const isShopPage = !isProductPage && (url.includes("shopee.vn/") && url.split('/').length >= 4 || url.includes("?shop=") || url.includes("/shop/"));

    initHUD();

    if (isProductPage) {
      updateHUD(`
        <div style="font-weight: 600; color: #f4f4f5; margin-bottom: 4px;">Phân tích Sản phẩm...</div>
        <div>Đang đọc thông tin sản phẩm từ trang Shopee.</div>
      `);
      
      // Delay slightly to allow SPA to render
      setTimeout(() => {
        const product = scrapeProductDetails();
        if (product.title) {
          sendProductToBackend(product);
        } else {
          updateHUD(`
            <div style="font-weight: 600; color: #f87171; margin-bottom: 4px;">⚠️ Chưa load xong dữ liệu</div>
            <div style="color: #e4e4e7;">Không thể lấy tiêu đề sản phẩm. Vui lòng nhấn nút bên dưới để thử lại.</div>
          `, "#f59e0b");
          clearHUDActions();
          addHUDAction("⚡ Trích xuất ngay", () => {
            const retryProduct = scrapeProductDetails();
            if (retryProduct.title) {
              sendProductToBackend(retryProduct);
            } else {
              alert("Không thể trích xuất sản phẩm. Vui lòng tải lại trang.");
            }
          }, true);
        }
      }, 2000);
    } else {
      updateHUD(`
        <div style="font-weight: 600; color: #f4f4f5; margin-bottom: 4px;">Trang cửa hàng Shopee 🛒</div>
        <div>Bạn có thể quét và cào toàn bộ sản phẩm của shop này về hệ thống.</div>
      `);
      clearHUDActions();
      addHUDAction("⚡ Quét & Gửi sản phẩm Shop này", scanShopProducts, true);
    }
  }

  // Run grabber when page is ready
  if (document.readyState === 'complete' || document.readyState === 'interactive') {
    setTimeout(executeGrabber, 1000);
  } else {
    window.addEventListener('DOMContentLoaded', () => {
      setTimeout(executeGrabber, 1000);
    });
  }

  // Listen for messages from popup/extension background
  if (typeof chrome !== 'undefined' && chrome.runtime && chrome.runtime.onMessage) {
    chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
      if (request.action === "re_crawl") {
        executeGrabber();
        sendResponse({status: "started"});
      }
      return true;
    });
  }

})();
