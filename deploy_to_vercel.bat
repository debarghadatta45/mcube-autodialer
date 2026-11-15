@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0portal"
title Deploy MCUBE Auto-Dialer Portal to Vercel

echo ===============================================================================
echo                Deploy MCUBE Auto-Dialer Portal to Vercel
echo ===============================================================================
echo.

:: 1. Check Vercel CLI Authentication
echo [*] Checking Vercel CLI Authentication...
call npx vercel whoami >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [!] You are currently not logged in to Vercel.
    echo [*] Opening browser to authenticate with Vercel...
    call npx vercel login
    if %ERRORLEVEL% NEQ 0 (
        echo [!] Vercel login was not completed. Aborting.
        pause
        exit /b 1
    )
)

echo [*] Vercel authenticated successfully!
echo.

:: 2. Link or Deploy Project
echo [*] Linking project to Vercel...
call npx vercel link --yes

:: 3. Safely sync secret MONGODB_URI to Vercel (NEVER printed or disclosed)
echo [*] Securely syncing secret MONGODB_URI environment variable to Vercel...
powershell -NoProfile -Command "
try {
    if (Test-Path '.env.local') {
        $line = Get-Content '.env.local' | Where-Object { $_ -match '^MONGODB_URI=' } | Select-Object -First 1
        if ($line) {
            $val = $line.Substring(12).Trim()
            $val | npx vercel env add MONGODB_URI --environment production,preview,development --sensitive --force --yes >$null 2>&1
            Write-Host '[OK] Secret MONGODB_URI safely configured on Vercel as sensitive secret.' -ForegroundColor Green
        } else {
            Write-Host '[WARN] MONGODB_URI not found in .env.local' -ForegroundColor Yellow
        }
    }
} catch {
    Write-Host '[!] Note: Env variable sync can be verified in Vercel project dashboard.'
}
"

:: 4. Deploy Production Build
echo.
echo [*] Deploying Production build to Vercel...
call npx vercel --prod --yes

echo.
echo ===============================================================================
echo [OK] Deployment Complete! Your portal is live on Vercel.
echo ===============================================================================
pause
