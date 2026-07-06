@echo off
chcp 65001 > nul
title Khởi động lại Chrome chính ở chế độ Debug
echo ========================================================
echo   LƯU Ý: Lệnh này sẽ đóng tạm thời các cửa sổ Chrome đang mở
echo   để khởi động lại Chrome chính của bạn ở chế độ Debug.
echo ========================================================
echo.
set /p choice="Bạn có muốn tiếp tục không? (Y/N): "
if /i "%choice%" neq "Y" goto end

echo Đang đóng các cửa sổ Chrome...
taskkill /f /im chrome.exe 2>nul
timeout /t 1 /nobreak >nul

echo Đang khởi động lại Chrome chính của bạn với cổng Debug 9222...
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222

echo.
echo ✅ THÀNH CÔNG!
echo Trình duyệt Chrome chính của bạn đã mở lại và hỗ trợ cào trực tiếp.
echo Bạn có thể vào Shopee (đã tự động đăng nhập sẵn) và nhấn nút Crawl ngay!
echo.
:end
pause
