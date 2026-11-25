@echo off
rem File nay CHI duoc chua ky tu ASCII (khong dau) - cmd doc sai file .bat co chu tieng Viet co dau.
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
for /d %%D in ("%~dp01-*") do set "DL_DIR=%%~fD"

echo ==================================================
echo                  TAI TRUYEN MOI
echo ==================================================
echo  1. truyencogiaothao  - dan link truyen (1 hoac nhieu link)
echo        luu vao: Truyen\2-truyencogiaothao
echo  2. truyensex18       - tu tai het truyen moi tren trang
echo        luu vao: Truyen\1-Text Mp3\Moi tai
echo  0. Thoat
echo --------------------------------------------------
echo  Truyen da co trong kho se tu bo qua.
echo  File ten bat dau bang "_" = co chuong tai loi.
echo ==================================================
set "c="
set /p c=Chon:

if "%c%"=="1" python "%DL_DIR%\leech_truyencogiaothao.py"
if "%c%"=="2" python "%DL_DIR%\leech_truyensex18.py"
if not "%c%"=="1" if not "%c%"=="2" exit /b

echo.
set "u="
set /p u=Cap nhat web luon (chia the loai + danh sach truyen)? (y/n):
if /i "%u%"=="y" for %%F in ("%~dp02.*.bat") do call "%%~fF" called
pause
