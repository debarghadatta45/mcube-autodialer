@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

title Chrome Remote Debugging Launcher - MCUBE / LeadSquared Auto-Dialer

echo ===============================================================================
echo        Google Chrome Remote Debugging Launcher (CDP Port 9222)
echo ===============================================================================
echo.

:: 1. Define Persistent Profile Directory
set "PROFILE_DIR=C:\chrome-autodial-profile"
if not exist "%PROFILE_DIR%" (
    echo [*] Creating persistent profile directory: %PROFILE_DIR%
    mkdir "%PROFILE_DIR%" >nul 2>&1
    if errorlevel 1 (
        echo [!] Warning: Could not create C:\chrome-autodial-profile.
        echo [*] Falling back to user directory: %USERPROFILE%\chrome-autodial-profile
        set "PROFILE_DIR=%USERPROFILE%\chrome-autodial-profile"
        if not exist "!PROFILE_DIR!" mkdir "!PROFILE_DIR!" >nul 2>&1
    )
) else (
    echo [*] Using existing profile directory: %PROFILE_DIR%
)

:: 2. Locate Google Chrome Executable
set "CHROME_EXE="

if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    set "CHROME_EXE=C:\Program Files\Google\Chrome\Application\chrome.exe"
) else if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" (
    set "CHROME_EXE=C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
) else if exist "%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe" (
    set "CHROME_EXE=%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"
) else (
    for /f "delims=" %%I in ('where chrome.exe 2^>nul') do (
        set "CHROME_EXE=%%I"
    )
)

if "%CHROME_EXE%"=="" (
    echo [ERROR] Google Chrome executable was not found in standard paths!
    echo Please install Google Chrome or update the path in this script.
    pause
    exit /b 1
)

echo [*] Chrome found at: "%CHROME_EXE%"

:: 3. Check if Port 9222 is already in use
netstat -ano | findstr /R /C:":9222 .*LISTENING" >nul 2>&1
if not errorlevel 1 (
    echo [!] Notice: Port 9222 is already active! A Chrome instance is already running with remote debugging.
    echo [*] Opening tabs in existing debugging session...
)

:: 4. Launch Chrome with CDP Flags and Target URLs
echo [*] Launching Chrome on http://localhost:9222 ...
echo [*] Initializing LeadSquared Opportunity Management and MCUBE Web Dialer...
echo.

start "" "%CHROME_EXE%" --remote-debugging-port=9222 --remote-allow-origins=* --user-data-dir="%PROFILE_DIR%" --no-first-run --no-default-browser-check --disable-background-networking --disable-background-timer-throttling --disable-renderer-backgrounding --disable-extensions --disable-sync --disable-translate --disable-default-apps --disable-notifications --metrics-recording-only --no-pings --disk-cache-size=52428800 --renderer-process-limit=3 --new-window "https://in21.leadsquared.com/OpportunityManagement?ec=12000" "https://dialer.mcube.com/index.html"

echo ===============================================================================
echo [*] Chrome has been launched successfully!
echo.
echo NEXT STEPS:
echo  1. Log in to LeadSquared and ensure you are on the Opportunity Management page.
echo  2. Log in to MCUBE Browser Phone and make sure the dialer is connected/ready.
echo  3. Run the Python Auto-Dialer:
echo        python autodialer.py
echo ===============================================================================
echo.
ping 127.0.0.1 -n 3 >nul 2>&1
exit /b 0

