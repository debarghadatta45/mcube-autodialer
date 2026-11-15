@echo off
setlocal
cd /d "%~dp0\portal"
title MCUBE Auto-Dialer - Web Portal

echo ===============================================================================
echo                MCUBE Auto-Dialer - Next.js Web Portal
echo ===============================================================================
echo.
echo [*] Starting Next.js Production Web Portal on http://localhost:3000...
echo [*] Press Ctrl+C to stop.
echo.

npm run start
pause
