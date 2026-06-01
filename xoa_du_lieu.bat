@echo off
chcp 65001 > nul
echo.
echo ==================================================
echo        CONG CU XOA DU LIEU TOOL (RESET)
echo ==================================================
echo.
echo CANH BAO: Hanh dong nay se xoa toan bo:
echo 1. Video da tai trong thu muc 'downloads'
echo 2. Lich su tai (lichsutaitiktok.txt)
echo 3. Hang doi cho tai (hangdoitiktok.txt)
echo 4. File log (automation.log)
echo.
echo.
echo Dang xoa du lieu...

if exist downloads (
    rmdir /s /q downloads
    echo [OK] Da xoa thu muc downloads
)

if exist lichsutaitiktok.txt (
    del lichsutaitiktok.txt
    echo [OK] Da xoa lichsutaitiktok.txt
)

if exist hangdoitiktok.txt (
    del hangdoitiktok.txt
    echo [OK] Da xoa hangdoitiktok.txt
)

if exist automation.log (
    del automation.log
    echo [OK] Da xoa automation.log
)

echo.
echo Hoan tat! Tool da tro ve trang thai moi.
exit
