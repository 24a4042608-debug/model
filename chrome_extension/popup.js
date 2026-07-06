document.addEventListener('DOMContentLoaded', () => {
  const apiUrlInput = document.getElementById('api-url');
  const saveBtn = document.getElementById('save-btn');
  const recrawlBtn = document.getElementById('recrawl-btn');
  const statusBox = document.getElementById('status-box');

  // Load saved API URL
  chrome.storage.local.get(['apiUrl'], (result) => {
    if (result.apiUrl) {
      apiUrlInput.value = result.apiUrl;
      testConnection(result.apiUrl);
    } else {
      apiUrlInput.value = 'http://localhost:8000';
      testConnection('http://localhost:8000');
    }
  });

  // Save API URL
  saveBtn.addEventListener('click', () => {
    let url = apiUrlInput.value.trim();
    if (!url) {
      url = 'http://localhost:8000';
    }
    // Remove trailing slash if exists
    if (url.endsWith('/')) {
      url = url.slice(0, -1);
    }
    
    chrome.storage.local.set({ apiUrl: url }, () => {
      statusBox.className = 'status idle';
      statusBox.innerText = 'Đang lưu và kết nối thử...';
      testConnection(url);
    });
  });

  // Recrawl tab
  recrawlBtn.addEventListener('click', () => {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (tabs[0]) {
        chrome.tabs.sendMessage(tabs[0].id, { action: "re_crawl" }, (response) => {
          if (chrome.runtime.lastError) {
            statusBox.className = 'status error';
            statusBox.innerText = 'Lỗi: Không tìm thấy content script Shopee ở tab này.';
          } else {
            statusBox.className = 'status success';
            statusBox.innerText = 'Đã gửi yêu cầu cào lại tới tab!';
          }
        });
      }
    });
  });

  // Test API server connection
  function testConnection(url) {
    fetch(`${url}/api/system-status`)
      .then(res => {
        if (res.ok) {
          statusBox.className = 'status success';
          statusBox.innerText = 'Kết nối Backend thành công! ✅';
        } else {
          statusBox.className = 'status error';
          statusBox.innerText = 'Kết nối lỗi: API phản hồi mã lỗi ⚠️';
        }
      })
      .catch(err => {
        statusBox.className = 'status error';
        statusBox.innerText = 'Không thể kết nối đến Backend API ❌';
      });
  }
});
