@echo off
chcp 65001 >nul
title Steam 客户端下载工具

echo.
echo   ╔═══════════════════════════════════════╗
echo   ║     Steam 客户端下载工具 v2.0         ║
echo   ╚═══════════════════════════════════════╝
echo.

cd /d "%~dp0"

powershell -Command "Start-Process python -ArgumentList 'steam_downloader.py' -Verb RunAs -WorkingDirectory '%~dp0'"

if %errorlevel% neq 0 (
    echo [错误] 启动失败，请确保已安装 Python。
    echo.
    echo 您也可以直接双击 steam_downloader.py 运行
    echo.
    pause
)
