# LeadSquared + MCUBE WebRTC Auto-Dialer

Production-ready local Python Playwright auto-dialer that attaches to an active Google Chrome session via Chrome DevTools Protocol (CDP) on `http://localhost:9222`.

Automates outbound dialing on **LeadSquared CRM** (`https://in21.leadsquared.com/OpportunityManagement?ec=12000`) paired with the **MCUBE Browser Phone** WebRTC popup (`dialer.mcube.com/index.html`).

---

## 📁 Project Architecture & Files

| File | Purpose |
| :--- | :--- |
| `start_autodialer.bat` | One-click launcher: checks port 9222, auto-launches Chrome if needed, activates `.venv`, and starts the auto-dialer. Supports starting from any page (e.g. `start_autodialer.bat 3`). |
| `launch_chrome.bat` | Windows batch script to launch Chrome with `--remote-debugging-port=9222` and persistent user profile at `C:\chrome-autodial-profile`. |
| `autodialer.py` | Main asynchronous automation engine with multi-page grid navigation, click-to-call, call confirmation handling, sub-stage filtering, and floating Tkinter controller. |
| `config.json` | Centralized JSON configuration for start page, target stages, excluded sub-stages, timeouts, and save keywords. |
| `sniff_mcube.py` | Diagnostic sniffer capturing WebSocket frames (high-level and raw CDP), Console logs, and XHR/Fetch requests to inspect and fine-tune Leg-B events. |
| `requirements.txt` | Core Python dependencies (`playwright`, `colorama`). |
| `.gitignore` | Standard Git ignore rules for virtual environments, caches, and session logs. |

---

## ⚡ Quick Start

### 1-Click Launch:
Run from Command Prompt or double-click:
```bat
start_autodialer.bat
```
To start directly from a specific page (e.g., Page 3):
```bat
start_autodialer.bat 3
```

- If Chrome is not already running on port 9222, it will automatically launch Chrome with the LeadSquared and MCUBE tabs.
- Log in to your LeadSquared CRM and MCUBE soft phone if needed.
- The floating mini-controller will open and dialing will begin automatically.

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
