@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0.."

echo ==================================================
echo            MỞ WEB ĐỌC TRUYỆN TRÊN MÁY
echo ==================================================
echo  Web:            http://127.0.0.1:8765
echo  Đọc giọng TTS:  cửa sổ "TTS proxy" (cổng 9999)
echo.
echo  Muốn tắt: đóng cửa sổ này + cửa sổ "TTS proxy".
echo ==================================================

start "TTS proxy" python "_Tool\6-Đọc truyện TTS\story_server.py"
start "" cmd /c "timeout /t 2 >nul & start http://127.0.0.1:8765/index.html"
python -m http.server 8765 --bind 127.0.0.1
