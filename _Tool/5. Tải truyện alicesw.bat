@echo off
rem File nay CHI duoc chua ky tu ASCII (khong dau) - cmd doc sai file .bat co chu tieng Viet co dau.
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
for /d %%D in ("%~dp01-*") do set "DL_DIR=%%~fD"
for %%A in ("%~dp0..\..\alicesw") do set "ALICE_DIR=%%~fA"

echo ==================================================
echo            TAI TRUYEN NGUON ALICESW (BAN GOC)
echo ==================================================
echo  Nguon:   alicesw - https://www.alicesw.com (tieng Trung)
echo  Luu vao: %ALICE_DIR%\downloaded\origin
echo.
echo  1. Tai truyen moi (tag me con)
echo  2. Truyen dang ra co chuong moi: chi tai chuong moi
echo  - CHUA dich. Dich + dua len web: chay "6. Dich truyen alicesw.bat"
echo  - Bi chan: tool tu doi IP qua WARP (mang ca may rot vai giay)
echo.
echo  Cua so tien do se hien len - dung tat cua so nay.
echo ==================================================
if not exist "%ALICE_DIR%\alicesw_downloader.py" (
    echo [!] Khong thay thu muc alicesw canh thu muc Audio: %ALICE_DIR%
    pause
    exit /b 1
)
python "%DL_DIR%\update_alicesw.py" --chi-tai
if errorlevel 1 pause
