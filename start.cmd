@echo off
cd /d "%~dp0"
pm2 start main.py --name "Gams Tiktok Downloader" --interpreter python
pause
