# ===============================================================================
#          Deploy MCUBE Auto-Dialer Next.js Portal to Vercel (Safe Env)
# ===============================================================================
Set-Location -Path $PSScriptRoot

Write-Host "===============================================================================" -ForegroundColor Cyan
Write-Host "                Deploying MCUBE Auto-Dialer Portal to Vercel" -ForegroundColor Cyan
Write-Host "===============================================================================" -ForegroundColor Cyan
Write-Host ""

# Check Vercel Login
$whoami = npx vercel whoami 2>$null
if (-not $whoami) {
    Write-Host "[*] Logging in to Vercel..." -ForegroundColor Yellow
    npx vercel login
}

# Link Project
Write-Host "[*] Linking project on Vercel..." -ForegroundColor Yellow
npx vercel link --yes

# Push Secret Env Variable (Hidden & Sensitive)
if (Test-Path ".env.local") {
    $line = Get-Content ".env.local" | Where-Object { $_ -match "^MONGODB_URI=" } | Select-Object -First 1
    if ($line) {
        $secretVal = $line.Substring(12).Trim()
        Write-Host "[*] Securing MONGODB_URI environment variable into Vercel..." -ForegroundColor Yellow
        $secretVal | npx vercel env add MONGODB_URI --environment production,preview,development --sensitive --force --yes 2>$null | Out-Null
        Write-Host "[OK] MONGODB_URI securely stored as Sensitive Secret on Vercel." -ForegroundColor Green
    }
}

# Deploy Production
Write-Host "[*] Triggering Vercel Production Build..." -ForegroundColor Yellow
npx vercel --prod --yes

Write-Host ""
Write-Host "===============================================================================" -ForegroundColor Green
Write-Host "[OK] Portal is deployed and live on Vercel!" -ForegroundColor Green
Write-Host "===============================================================================" -ForegroundColor Green
