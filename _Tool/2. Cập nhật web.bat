@echo off
rem File nay CHI duoc chua ky tu ASCII (khong dau) - cmd doc sai file .bat co chu tieng Viet co dau.
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
for /d %%D in ("%~dp02-*") do set "WEB_DIR=%%~fD"

echo ==================================================
echo              CAP NHAT WEB DOC TRUYEN
echo ==================================================
echo.
echo [1/3] Chia the loai cho truyen moi tai (truyencogiaothao)...
python "%WEB_DIR%\auto_sort_giaothao.py"

echo.
echo [2/3] Tao lai danh sach truyen (stories.json)...
python "%WEB_DIR%\update_index.py"

echo.
echo [3/3] Dua len GitHub de web online cap nhat
cd /d "%~dp0.."
git -c core.quotepath=false status --short -- stories.json "Truy*"
set "p="
set /p p=Push len GitHub? (y/n):
if /i "%p%"=="y" (
    git add -A -- stories.json "Truy*"
    git commit -m "Cap nhat truyen moi"
    git push
)

echo.
echo Xong!
if "%~1"=="" pause
