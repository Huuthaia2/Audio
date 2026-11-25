@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"

echo ==================================================
echo                 TẢI TRUYỆN MỚI
echo ==================================================
echo  1. truyencogiaothao  - dán link truyện (1 hoặc nhiều link)
echo        lưu vào: Truyện\2-truyencogiaothao
echo  2. truyensex18       - tự tải hết truyện mới trên trang
echo        lưu vào: Truyện\1-Text Mp3\Mới tải
echo  0. Thoát
echo --------------------------------------------------
echo  Truyện đã có trong kho sẽ tự bỏ qua.
echo  File tên bắt đầu bằng "_" = có chương tải lỗi.
echo ==================================================
set "c="
set /p c=Chọn:

if "%c%"=="1" python "1-Tải truyện\leech_truyencogiaothao.py"
if "%c%"=="2" python "1-Tải truyện\leech_truyensex18.py"
if not "%c%"=="1" if not "%c%"=="2" exit /b

echo.
set "u="
set /p u=Cập nhật web luôn (chia thể loại + danh sách truyện)? (y/n):
if /i "%u%"=="y" call "2. Cập nhật web.bat" called
pause
