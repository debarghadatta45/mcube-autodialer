@echo off
setlocal
cd /d "%~dp0"
title MCUBE + LeadSquared Auto-Dialer

echo ===============================================================================
echo                MCUBE + LeadSquared Auto-Dialer Launcher
echo ===============================================================================
echo.

:: 1. Check if Chrome is listening on port 9222
netstat -ano | findstr /R /C:":9222 .*LISTENING" >nul 2>&1
if errorlevel 1 (
    echo [*] Chrome is not running on port 9222.
    echo [*] Automatically launching Google Chrome...
    call launch_chrome.bat
    echo.
    echo [*] Waiting 4 seconds for Chrome to initialize...
    ping 127.0.0.1 -n 5 >nul 2>&1
) else (
    echo [*] Chrome is already running with remote debugging on port 9222.
)

:: 2. Check virtual environment
if not exist ".venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment was not found in .venv!
    echo Please run 'pip install -r requirements.txt'
    pause
    exit /b 1
)

echo.
echo [*] Activating virtual environment...
call ".venv\Scripts\activate.bat"

echo [*] Starting Auto-Dialer with floating mini-controller...
echo.

if "%~1"=="" (
    python autodialer.py
) else (
    echo [*] Starting from requested Page %~1...
    python autodialer.py --page %~1
)

echo.
echo [*] Auto-Dialer exited.
pause
