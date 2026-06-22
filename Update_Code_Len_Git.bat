@echo off
title Update Code Len GitHub
cd /d "%~dp0"
echo ====================================================
echo   TIEN TRINH UPLOAD CODE LEN GITHUB
echo ====================================================
echo.

:: 1. Kiem tra phan mem Git
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [LOI] May tinh cua ban chua cai dat Git.
    echo Vui long cai dat Git tai: https://git-scm.com/
    pause
    exit /b
)

:: 2. Show trang thai
echo [1] Trang thai thay doi hien tai:
git status -s
echo.

:: 3. Them tat ca cac file thay doi
echo [2] Dang them cac file vao Git Stage...
git add .

:: 4. Nhap noi dung Commit
set /p commit_msg="Nhap noi dung commit (Enter de dung: 'Update code tu dong'): "
if "%commit_msg%"=="" set commit_msg=Update code tu dong

:: 5. Commit
echo.
echo [3] Dang commit: "%commit_msg%"...
git commit -m "%commit_msg%"

:: 6. Push
echo.
echo [4] Dang day code len GitHub (origin/main)...
git push origin main
if %errorlevel% equ 0 (
    echo.
    echo ====================================================
    echo   GUI CODE LEN GITHUB THANH CONG!
    echo ====================================================
) else (
    echo.
    echo ====================================================
    echo   [LOI] Khong the day code len GitHub.
    echo   Vui long kiem tra ket noi mang va quyen truy cap.
    echo ====================================================
)
pause
