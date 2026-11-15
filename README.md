# LeadSquared + MCUBE WebRTC Auto-Dialer

Production-ready local Python Playwright auto-dialer that attaches to an active Google Chrome session via Chrome DevTools Protocol (CDP) on `http://localhost:9222`.

Automates outbound dialing on **LeadSquared CRM** (`https://in21.leadsquared.com/OpportunityManagement?ec=12000`) paired with the **MCUBE Browser Phone** WebRTC popup (`dialer.mcube.com/index.html`).

---

## 📁 Project Architecture & Files

| File | Purpose |
| :--- | :--- |
| `MCUBE_AutoDialer.exe` | Standalone double-clickable Windows application (located in `dist/MCUBE_AutoDialer/`). |
| `start_mac.command` | Standalone double-clickable macOS Finder launcher (automatically sets up environment and runs). |
| `MCUBE_AutoDialer.app` | Native macOS Application Bundle. |
| `build_windows.bat` | One-click script to build standalone Windows `.exe` and package `MCUBE_AutoDialer_Windows.zip`. |
| `build_mac.sh` | One-command script to build native macOS binary and package `MCUBE_AutoDialer_macOS.zip`. |
| `.github/workflows/build_apps.yml` | GitHub Actions workflow automatically building Windows & macOS apps in the cloud. |
| `start_autodialer.bat` | Windows batch launcher for running directly from source code. |
| `launch_chrome.bat` | Standalone Chrome launcher for port 9222. |
| `autodialer.py` | Cross-platform automation engine (Windows & macOS) with auto-detecting Chrome, multi-page pagination, click-to-call, confirmation handling, sub-stage filtering, and floating controller. |
| `config.json` | Centralized JSON configuration for start page, target stages, excluded sub-stages, timeouts, and save keywords. |
| `requirements.txt` | Core Python dependencies (`playwright`, `colorama`). |

---

## ⚡ How to Run

### 🪟 On Windows:

#### Option 1: Standalone Application (.exe)
1. Extract `dist/MCUBE_AutoDialer_Windows.zip` or open folder `dist/MCUBE_AutoDialer/`.
2. Double-click **`MCUBE_AutoDialer.exe`**.
3. The app automatically detects if Google Chrome is running on port 9222. If not, it launches Chrome automatically with your session profile!
4. The floating mini-controller pops up and auto-dialing begins.

#### Option 2: Run from Source / Batch Script
Double-click:
```bat
start_autodialer.bat
```
To start directly from a specific page (e.g. Page 3):
```bat
start_autodialer.bat 3
```

---

### 🍏 On macOS:

#### Option 1: Finder Double-Click Launcher
1. Simply double-click **`start_mac.command`** in Finder (or launch `MCUBE_AutoDialer.app`).
2. *First-time permission (if prompted by macOS Gatekeeper)*: Open Terminal and run:
   ```bash
   chmod +x start_mac.command MCUBE_AutoDialer.app/Contents/MacOS/MCUBE_AutoDialer
   ```
3. It will automatically check Python 3, create the isolated environment, install dependencies, launch Google Chrome on port 9222, and display the floating mini-controller.

#### Option 2: Build Standalone macOS App
To compile the standalone macOS binary locally on any Mac:
```bash
chmod +x build_mac.sh
./build_mac.sh
```
This generates `dist/MCUBE_AutoDialer` and `dist/MCUBE_AutoDialer_macOS.zip`.

---

### ☁️ Cloud Dual-OS Builds (GitHub Actions):
Every push to `main` automatically triggers `.github/workflows/build_apps.yml` on GitHub Actions, which compiles native builds on both `windows-latest` and `macos-latest` runners and provides ready-to-download `.zip` application packages.

---

## 🚀 Key Features

1. **Exact LeadSquared Opportunity Navigation:**
   - Clicks only the Opportunity Name link in Column 2 (`a[href*='OpportunityDetails']`), preventing accidental redirection to contact profile views.
   - On the Details view, identifies the exact `onLeadDetailsNumberClick` phone link.
   - Automatically clicks **"Yes"** on the confirmation dialog to initiate the call.

2. **Automated Multi-Page Grid Pagination:**
   - Automatically advances across pages (Page 1 → Page 2 → Page 3 → ...).
   - If returning from a call resets the grid back to Page 1, it automatically detects the mismatch and returns to the active page.
   - Remembers the last page dialed in `session_state.json` so you never lose your place after restarting.

3. **Smart Sub-Stage Filtering:**
   - Inspects `Sub Stage` and `Super Sub Stage` before placing the call.
   - Automatically skips leads marked **"Invalid Lead"**, **"Not Interested"**, or **"User registered by mistake"** and returns cleanly to the grid.

4. **Floating Mini-Controller Widget:**
   - Always-on-top Tkinter control bar with live status, lead details, call counts, and controls:
     - `Page: [ 1 ] [Go] [◀ Prev] [Next ▶]` — Jump to or step through pages anytime while running.
     - `📞 Customer Answered` — Immediately marks Leg B connected.
     - `💾 Disposition Done (Resume)` — Resumes dialing after disposition save.
     - `⏭ Skip` — Skips current lead without dialing.
     - `⏸ Pause` / `🛑 Stop` — Non-destructive controls keeping Chrome open.

---

## ⚙️ Configuration (`config.json`)

```json
{
  "start_page": 1,
  "cdp_url": "http://localhost:9222",
  "lsq_manage_url": "https://in21.leadsquared.com/OpportunityManagement?ec=12000",
  "target_stages": [
    "Non Contact",
    "Assigned",
    "Open - Assigned",
    "Open Assigned",
    "Open",
    "New"
  ],
  "exclude_sub_stages": [
    "Invalid Lead",
    "Not Interested",
    "Invalid",
    "User registered by mistake"
  ],
  "ring_timeout_seconds": 38,
  "delay_between_calls": 2.0
}
```
