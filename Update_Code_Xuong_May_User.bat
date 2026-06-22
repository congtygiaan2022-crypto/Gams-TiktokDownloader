@echo off
title Cap Nhat Code Tu GitHub Xuong May
cd /d "%~dp0"
echo ====================================================
echo   TIEN TRINH CAP NHAT CODE MOI NHAT TU GITHUB
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

:: 2. Khoi tao Git neu chua co
if not exist ".git" (
    echo [THONG BAO] Chua thay kho Git. Tien hanh khoi tao...
    git init
    git remote add origin https://github.com/congtygiaan2022-crypto/Gams-TiktokDownloader.git
) else (
    git remote set-url origin https://github.com/congtygiaan2022-crypto/Gams-TiktokDownloader.git
)

:: 3. fetch va pull
echo [1] Dang dong bo ma nguon tu GitHub...
git fetch --all
git reset --hard origin/main

if %errorlevel% equ 0 (
    echo.
    echo [2] Dang tu dong kiem tra va cap nhat thu vien Python...
    if exist "requirements.txt" (
        pip install -r requirements.txt
    )
    echo.
    echo ====================================================
    echo   CAP NHAT MA NGUON THANH CONG!
    echo   Ban da dong bo phien ban moi nhat.
    echo ====================================================
) else (
    echo.
    echo ====================================================
    echo   [LOI] Dong bo ma nguon tu GitHub that bai.
    echo   Vui long kiem tra ket noi Internet.
    echo ====================================================
)
pause
