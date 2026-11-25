@echo off
rem File nay CHI duoc chua ky tu ASCII (khong dau) - cmd doc sai file .bat co chu tieng Viet co dau.
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
for /d %%D in ("%~dp01-*") do set "DL_DIR=%%~fD"

echo ==================================================
echo             TU DONG CAP NHAT TRUYEN
echo ==================================================
echo  Nguon:   truyencogiaothao - https://truyencogiaothaox.net
echo  Luu vao: Truyen\2-truyencogiaothao
echo.
echo  - Noi chuong moi cho truyen da co + tai truyen moi dang
echo  - Xong tu chia the loai + lam lai stories.json (KHONG push)
echo  - Muon dua len web online: chay "2. Cap nhat web.bat"
echo.
echo  Cua so tien do se hien len - dung tat cua so nay.
echo ==================================================
python "%DL_DIR%\update_truyencogiaothao.py"
if errorlevel 1 pause
