@echo off
echo Dang kiem tra va cai dat PyInstaller...
python -m pip install pyinstaller

set /p icon_path="Nhap duong dan file icon (.ico) hoac de trong de dung icon mac dinh: "

:: Loai bo dau ngoac kep neu nguoi dung nhap vao (vi du khi Copy as path)
set "icon_path=%icon_path:"=%"

if "%icon_path%"=="" (
    echo Dang build EXE voi icon mac dinh...
    python -m PyInstaller --noconfirm --onefile --windowed "GiaanTesttool.py"
) else (
    echo Dang build EXE voi icon: %icon_path%
    python -m PyInstaller --noconfirm --onefile --windowed --icon="%icon_path%" "GiaanTesttool.py"
)

echo.
if exist "dist\GiaanTesttool.exe" (
    echo.
    echo ==================================================
    echo HOAN TAT! File EXE nam trong thu muc 'dist'.
    echo ==================================================
) else (
    echo.
    echo [LOI] Khong tim thay file EXE trong thu muc 'dist'. 
    echo Vui long kiem tra xem file 'GiaanTesttool.py' co nam cung thu muc voi file .bat nay khong.
)
pause
