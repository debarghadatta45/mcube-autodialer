@echo off
setlocal
cd /d "%~dp0"
title MCUBE + LeadSquared - 1-Click Master Launcher

echo ===============================================================================
echo            MCUBE + LeadSquared Auto-Dialer (1-Click Master Launcher)
echo ===============================================================================
echo.

echo [1/2] Launching Google Chrome on port 9222...
call launch_chrome.bat

echo.
echo [*] Waiting 3 seconds for Chrome to initialize...
ping 127.0.0.1 -n 4 >nul 2>&1

echo.
echo [2/2] Starting Auto-Dialer foreground process and floating controller...
start "MCUBE Auto-Dialer Controller" cmd /k "cd /d "%~dp0" && call .venv\Scripts\activate.bat && python autodialer.py"

echo.
echo ===============================================================================
echo [SUCCESS] Chrome and Auto-Dialer launched!
echo.
echo 1. In the Chrome window, log in to LeadSquared and MCUBE.
echo 2. The Auto-Dialer will automatically detect your login and start dialing!
echo ===============================================================================
echo.
ping 127.0.0.1 -n 3 >nul 2>&1
exit /b 0
