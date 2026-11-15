#!/bin/bash
# ===============================================================================
#             MCUBE Auto-Dialer - macOS Standalone App Builder
# ===============================================================================
set -e
cd "$(dirname "$0")"

echo "==============================================================================="
echo "                MCUBE Auto-Dialer - macOS App Builder"
echo "==============================================================================="
echo ""

if ! command -v python3 &> /dev/null; then
    echo "[!] Python 3 not found. Please install Python 3 first."
    exit 1
fi

if [ ! -d ".venv_mac" ]; then
    echo "[*] Creating virtual environment (.venv_mac)..."
    python3 -m venv .venv_mac
fi

source .venv_mac/bin/activate
echo "[*] Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt pyinstaller
python3 -m playwright install chromium

echo "[*] Building macOS Application Bundle via PyInstaller..."
pyinstaller --noconfirm --onedir --windowed \
    --name "MCUBE_AutoDialer" \
    --collect-all playwright \
    autodialer.py

echo "[*] Copying configuration..."
cp config.json dist/MCUBE_AutoDialer/config.json 2>/dev/null || true
cp -r dist/MCUBE_AutoDialer.app dist/ 2>/dev/null || true

echo "[*] Creating macOS ZIP Archive..."
cd dist
zip -r MCUBE_AutoDialer_macOS.zip MCUBE_AutoDialer*
cd ..

echo "==============================================================================="
echo "[OK] macOS Build Complete! Artifacts in dist/"
echo "==============================================================================="
