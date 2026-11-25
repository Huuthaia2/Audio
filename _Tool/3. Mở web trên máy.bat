@echo off
rem File nay CHI duoc chua ky tu ASCII (khong dau) - cmd doc sai file .bat co chu tieng Viet co dau.
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
for /d %%D in ("%~dp06-*") do set "TTS_DIR=%%~fD"
cd /d "%~dp0.."

echo ==================================================
echo            MO WEB DOC TRUYEN TREN MAY
echo ==================================================
echo  Web:            http://127.0.0.1:8765
echo  Doc giong TTS:  cua so "TTS proxy" (cong 9999)
echo.
echo  Muon tat: dong cua so nay + cua so "TTS proxy".
echo ==================================================

start "TTS proxy" python "%TTS_DIR%\story_server.py"
start "" cmd /c "timeout /t 2 >nul & start http://127.0.0.1:8765/index.html"
rem Web server tu dung (loi, mat ket noi...) => tu chay lai sau 2 giay. Muon tat han: dong cua so nay.
:serve
python -m http.server 8765 --bind 127.0.0.1
echo.
echo  [!] Web server vua dung - tu chay lai sau 2 giay (dong cua so nay de tat han)...
timeout /t 2 >nul
goto serve
