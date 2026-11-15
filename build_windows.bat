@echo off
setlocal
cd /d "%~dp0"
title MCUBE Auto-Dialer Windows App Builder

echo ===============================================================================
echo                MCUBE Auto-Dialer - Windows Application Builder
echo ===============================================================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo [*] Virtual environment not found. Setting up...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    pip install -r requirements.txt pyinstaller
) else (
    call .venv\Scripts\activate.bat
)

echo [*] Building Standalone Windows Executable (.exe) with PyInstaller...
python -m PyInstaller --noconfirm --onedir --windowed --name "MCUBE_AutoDialer" --collect-all playwright autodialer.py

if %ERRORLEVEL% NEQ 0 (
    echo [!] PyInstaller build failed!
    pause
    exit /b %ERRORLEVEL%
)

echo [*] Copying configuration files to dist\MCUBE_AutoDialer...
copy /y config.json dist\MCUBE_AutoDialer\config.json >nul
copy /y session_state.json dist\MCUBE_AutoDialer\session_state.json >nul 2>&1
copy /y launch_chrome.bat dist\MCUBE_AutoDialer\launch_chrome.bat >nul

echo [*] Creating Windows ZIP Archive: dist\MCUBE_AutoDialer_Windows.zip...
powershell -Command "Compress-Archive -Path 'dist\MCUBE_AutoDialer\*' -DestinationPath 'dist\MCUBE_AutoDialer_Windows.zip' -Force"

echo.
echo ===============================================================================
echo [OK] Windows Build Complete!
echo      - Executable: dist\MCUBE_AutoDialer\MCUBE_AutoDialer.exe
echo      - Standalone ZIP: dist\MCUBE_AutoDialer_Windows.zip
echo ===============================================================================
pause
