@echo off
cd /d "%~dp0"
echo ====================================================
echo   KHOI CHAY CONG CU UPLOAD GIT CHUYEN NGHIEP...
echo ====================================================
echo.
python Upload_Git.py
if %errorlevel% neq 0 (
    echo.
    echo ====================================================
    echo   [LOI] Khong the khoi chay cong cu Upload.
    echo   Vui long kiem tra xem Python da duoc cai dat chua.
    echo ====================================================
    echo.
    pause
)
