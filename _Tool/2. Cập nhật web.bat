@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"

echo ==================================================
echo                 CẬP NHẬT WEB ĐỌC TRUYỆN
echo ==================================================
echo.
echo [1/3] Chia thể loại cho truyện mới tải (truyencogiaothao)...
python "2-Cập nhật web\auto_sort_giaothao.py"

echo.
echo [2/3] Tạo lại danh sách truyện (stories.json)...
python "2-Cập nhật web\update_index.py"

echo.
echo [3/3] Đưa lên GitHub để web online cập nhật
cd /d "%~dp0.."
git status --short -- Truyện stories.json
set "p="
set /p p=Push lên GitHub? (y/n):
if /i "%p%"=="y" (
    git add -A -- Truyện stories.json
    git commit -m "Cập nhật truyện mới"
    git push
)

echo.
echo Xong!
if "%~1"=="" pause
