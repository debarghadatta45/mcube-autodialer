@echo off
setlocal
title MCUBE Dialer Diagnostic Sniffer

echo ===============================================================================
echo                MCUBE WebRTC & SIP Diagnostic Sniffer Launcher
echo ===============================================================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment was not found in .venv!
    echo Please set up the environment or run 'pip install -r requirements.txt'
    pause
    exit /b 1
)

echo [*] Starting diagnostic sniffer...
echo [*] Ensure Chrome is running on port 9222 via 'launch_chrome.bat' and MCUBE dialer is open.
echo.

".venv\Scripts\python.exe" sniff_mcube.py

echo.
echo [*] Sniffer finished.
pause

