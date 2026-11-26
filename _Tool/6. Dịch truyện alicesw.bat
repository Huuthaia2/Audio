@echo off
rem File nay CHI duoc chua ky tu ASCII (khong dau) - cmd doc sai file .bat co chu tieng Viet co dau.
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
for /d %%D in ("%~dp01-*") do set "DL_DIR=%%~fD"
for %%A in ("%~dp0..\..\alicesw") do set "ALICE_DIR=%%~fA"

echo ==================================================
echo            DICH TRUYEN NGUON ALICESW
echo ==================================================
echo  Nguon:   %ALICE_DIR%\downloaded\origin (tieng Trung)
echo  Dich:    Google, 3 truyen cung luc
echo  Luu vao: %ALICE_DIR%\downloaded	ranslated
echo.
echo  3. Dich ban goc moi / co chuong moi (chi dich chuong moi)
echo  4. Dong bo Truyen-alicesw + lam lai stories.json (KHONG push)
echo  - Muon dua len web online: chay "2. Cap nhat web.bat"
echo.
echo  Cua so tien do se hien len - dung tat cua so nay.
echo ==================================================
if not exist "%ALICE_DIR%\alicesw_downloader.py" (
    echo [!] Khong thay thu muc alicesw canh thu muc Audio: %ALICE_DIR%
    pause
    exit /b 1
)
python "%DL_DIR%\update_alicesw.py" --chi-dich
if errorlevel 1 pause
