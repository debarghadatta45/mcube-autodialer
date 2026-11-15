#!/bin/bash
# ===============================================================================
#             MCUBE + LeadSquared Auto-Dialer (macOS Launcher)
# ===============================================================================
cd "$(dirname "$0")"

echo "==============================================================================="
echo "                MCUBE + LeadSquared Auto-Dialer for macOS"
echo "==============================================================================="
echo ""

# Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo "[!] Python 3 was not found on your Mac."
    echo "[*] Please install Python 3 from https://www.python.org or run: brew install python"
    read -p "Press Enter to exit..."
    exit 1
fi

# Setup Virtual Environment if not present
if [ ! -d ".venv_mac" ]; then
    echo "[*] Initializing macOS virtual environment (.venv_mac)..."
    python3 -m venv .venv_mac
    source .venv_mac/bin/activate
    echo "[*] Installing required packages..."
    pip install --upgrade pip
    pip install -r requirements.txt
    python3 -m playwright install chromium
else
    source .venv_mac/bin/activate
fi

# Auto-launch Chrome if port 9222 is not open
if ! nc -z 127.0.0.1 9222 2>/dev/null; then
    echo "[*] Launching Google Chrome on port 9222..."
    CHROME_APP="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    PROFILE_DIR="$HOME/chrome-autodial-profile"
    mkdir -p "$PROFILE_DIR"
    
    if [ -f "$CHROME_APP" ]; then
        "$CHROME_APP" \
            --remote-debugging-port=9222 \
            --user-data-dir="$PROFILE_DIR" \
            --no-first-run \
            --no-default-browser-check \
            "https://in21.leadsquared.com/OpportunityManagement?ec=12000" \
            "https://dialer.mcube.com/index.html" >/dev/null 2>&1 &
        sleep 2
    else
        echo "[WARN] Google Chrome not found at /Applications/Google Chrome.app"
        echo "[WARN] Please open Chrome manually with --remote-debugging-port=9222"
    fi
fi

echo "[*] Starting Auto-Dialer with floating mini-controller..."
if [ -f "MCUBE_AutoDialer.app/Contents/MacOS/autodialer.pyc" ]; then
    python3 MCUBE_AutoDialer.app/Contents/MacOS/autodialer.pyc
elif [ -f "autodialer.pyc" ]; then
    python3 autodialer.pyc
else
    python3 autodialer.py
fi

echo ""
echo "[*] Auto-Dialer finished."
read -p "Press Enter to close this window..."
