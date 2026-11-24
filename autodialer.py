#!/usr/bin/env python3
"""
LeadSquared + MCUBE Auto-Dialer v4 (Final Production)
=====================================================
Target URL: https://in21.leadsquared.com/OpportunityManagement?ec=12000
Dialer URL: https://dialer.mcube.com/index.html

Fully verified on live LeadSquared DOM:
  1. Grid: Locates leads with matching stages and clicks 'a[href*='OpportunityDetails']'
  2. Details: Calls click-to-call via 'a[onclick*='onLeadDetailsNumberClick']'
  3. Confirmation: Clicks 'Yes' on the placement modal to initiate the call
  4. MCUBE Soft Phone: Tracks WebRTC call status in real-time
  5. Return: Executes 'GoBackToSource()' to return to the grid for the next lead
"""

import asyncio
import datetime
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import threading
import time
import tkinter as tk
from typing import Optional

from playwright.async_api import async_playwright, Page, Browser

try:
    import winsound
except ImportError:
    winsound = None

# ============================================================
# APP DIRECTORY & LOGGING CONFIGURATION
# ============================================================
if getattr(sys, "frozen", False):
    APP_DIR = os.path.dirname(sys.executable)
    # If running inside macOS .app bundle, point to folder containing the .app
    if sys.platform == "darwin" and ".app/Contents/MacOS" in APP_DIR:
        APP_DIR = os.path.abspath(os.path.join(APP_DIR, "../../.."))
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_PATH = os.path.join(APP_DIR, "config.json")
STATE_PATH = os.path.join(APP_DIR, "session_state.json")
LOG_PATH = os.path.join(APP_DIR, "autodialer.log")

class _FileLogger:
    def __init__(self, filepath):
        self.filepath = filepath
    def write(self, data):
        try:
            with open(self.filepath, "a", encoding="utf-8", errors="replace") as f:
                f.write(data)
        except Exception:
            pass
    def flush(self):
        pass

if sys.stdout is None:
    sys.stdout = _FileLogger(LOG_PATH)
if sys.stderr is None:
    sys.stderr = _FileLogger(LOG_PATH)

# ============================================================
# CONFIGURATION
# ============================================================
CDP_URL = "http://localhost:9222"
LSQ_MANAGE_URL = "https://in21.leadsquared.com/OpportunityManagement?ec=12000"

START_PAGE = 1
TARGET_STAGES = [
    "Non Contact",
    "Assigned",
    "Open - Assigned",
    "Open Assigned",
    "Open",
    "New",
    "Lead Connected"
]
EXCLUDE_SUB_STAGES = [
    "Open - Demo Done",
    "Demo Done",
    "Wave Form not filled",
    "Waveform not filled",
    "Wave Form",
    "Waveform",
    "Language Barrier",
    "Language Barier",
    "Invalid Lead",
    "Not Interested",
    "Invalid",
    "User registered by mistake"
]
RING_TIMEOUT = 38         # seconds before marking DNP
DELAY_AFTER_DNP = 2       # seconds pause between calls
DELAY_AFTER_CONNECTED = 2 # seconds after disposition before next call

if os.path.exists(CONFIG_PATH):
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as _f:
            _cfg = json.load(_f)
            START_PAGE = int(_cfg.get("start_page", START_PAGE))
            TARGET_STAGES = _cfg.get("target_stages", TARGET_STAGES)
            EXCLUDE_SUB_STAGES = _cfg.get("exclude_sub_stages", EXCLUDE_SUB_STAGES)
            RING_TIMEOUT = _cfg.get("ring_timeout_seconds", RING_TIMEOUT)
            DELAY_AFTER_DNP = _cfg.get("delay_between_calls", DELAY_AFTER_DNP)
    except Exception:
        pass

# Command line argument override: --page <N>
for _idx, _arg in enumerate(sys.argv):
    if _arg in ("--page", "-p") and _idx + 1 < len(sys.argv):
        try:
            START_PAGE = int(sys.argv[_idx + 1])
        except ValueError:
            pass


def ts():
    return datetime.datetime.now().strftime("%H:%M:%S")

def log(msg, level="INFO"):
    colors = {
        "INFO": "",
        "OK": "\033[92m",
        "WARN": "\033[93m",
        "ERR": "\033[91m",
        "CALL": "\033[96m"
    }
    reset = "\033[0m"
    c = colors.get(level, "")
    line = f"[{ts()}] [{level}] {msg}"
    formatted = f"[{ts()}] {c}[{level}]{reset} {msg}"
    try:
        print(formatted)
    except Exception:
        pass
    try:
        with open(LOG_PATH, "a", encoding="utf-8", errors="replace") as _lf:
            _lf.write(line + "\n")
    except Exception:
        pass

def is_port_open(host="127.0.0.1", port=9222):
    """Check if remote debugging port is open."""
    try:
        with socket.create_connection((host, port), timeout=1.0):
            return True
    except OSError:
        return False

def get_chrome_executable():
    """Locate Google Chrome executable across Windows and macOS."""
    if sys.platform == "win32":
        # 1. Check Windows Registry
        try:
            import winreg
            for root_key in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
                for subkey in (
                    r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe",
                    r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe"
                ):
                    try:
                        with winreg.OpenKey(root_key, subkey) as k:
                            val, _ = winreg.QueryValueEx(k, "")
                            if val and os.path.isfile(val):
                                return val
                    except OSError:
                        pass
        except Exception:
            pass

        # 2. Check Standard Directory Paths
        candidates = [
            os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), "Google", "Chrome", "Application", "chrome.exe"),
            os.path.join(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"), "Google", "Chrome", "Application", "chrome.exe"),
            os.path.join(os.environ.get("ProgramW6432", r"C:\Program Files"), "Google", "Chrome", "Application", "chrome.exe"),
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Google", "Chrome", "Application", "chrome.exe"),
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
        ]
        for p in candidates:
            if p and os.path.isfile(p):
                return p

        # 3. Check PATH
        for c in ["chrome.exe", "chrome"]:
            f = shutil.which(c)
            if f and os.path.isfile(f):
                return f

    elif sys.platform == "darwin":
        candidates = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            os.path.expanduser("~/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
        ]
        for p in candidates:
            if os.path.isfile(p):
                return p
        for c in ["google-chrome", "chromium"]:
            f = shutil.which(c)
            if f:
                return f
    else:
        for cmd in ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser"]:
            found = shutil.which(cmd)
            if found:
                return found
    return None

def auto_launch_chrome():
    """Ensure Chrome is running with remote debugging port 9222 and open LS + MCUBE."""
    chrome_bin = get_chrome_executable()

    if sys.platform == "win32":
        base_dir = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
        profile_dir = os.path.join(base_dir, "MCUBE_AutoDialer", "chrome-profile")
    else:
        profile_dir = os.path.expanduser("~/chrome-autodial-profile")

    try:
        os.makedirs(profile_dir, exist_ok=True)
    except Exception as e:
        log(f"Profile directory notice: {e}", "WARN")

    if not is_port_open("127.0.0.1", 9222):
        if not chrome_bin:
            log("Google Chrome binary not found! Please install Chrome or launch it manually with port 9222.", "ERR")
            return False

        log("Auto-launching Google Chrome on port 9222 with LS and MCUBE tabs...", "INFO")
        try:
            if sys.platform == "win32":
                cmd = f'start "" "{chrome_bin}" --remote-debugging-port=9222 --remote-allow-origins=* --user-data-dir="{profile_dir}" --no-first-run --no-default-browser-check --new-window "{LSQ_MANAGE_URL}" "https://dialer.mcube.com/index.html"'
                subprocess.Popen(cmd, shell=True)
            elif sys.platform == "darwin":
                subprocess.Popen([
                    chrome_bin,
                    "--remote-debugging-port=9222",
                    "--remote-allow-origins=*",
                    f"--user-data-dir={profile_dir}",
                    "--no-first-run",
                    "--no-default-browser-check",
                    "--new-window",
                    LSQ_MANAGE_URL,
                    "https://dialer.mcube.com/index.html"
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                subprocess.Popen([
                    chrome_bin,
                    "--remote-debugging-port=9222",
                    "--remote-allow-origins=*",
                    f"--user-data-dir={profile_dir}",
                    "--no-first-run",
                    "--no-default-browser-check",
                    "--new-window",
                    LSQ_MANAGE_URL,
                    "https://dialer.mcube.com/index.html"
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            log(f"Failed to auto-launch Chrome: {e}", "ERR")
            return False

        # Wait up to 15 seconds for port 9222 to become available
        for _ in range(15):
            time.sleep(1)
            if is_port_open("127.0.0.1", 9222):
                log("Google Chrome is now running and listening on port 9222!", "OK")
                return True

        return False
    else:
        log("Google Chrome is already listening on port 9222.", "OK")
        return True

def play_connected_chime():
    """Cross-platform audible alert when call connects."""
    try:
        if sys.platform == "win32" and winsound:
            winsound.Beep(1000, 300)
            winsound.Beep(1400, 200)
        elif sys.platform == "darwin":
            subprocess.Popen(["afplay", "/System/Library/Sounds/Glass.aiff"])
        else:
            print("\a", end="", flush=True)
    except Exception:
        pass


# ============================================================
# FLOATING MINI-CONTROLLER (Tkinter Always-on-Top)
# ============================================================
class MiniController:
    def __init__(self, loop, initial_page=1):
        self.loop = loop
        self.stopped = False
        self.paused = False
        self.retry_connect_requested = False
        self.customer_answered = asyncio.Event()
        self.skip_lead = asyncio.Event()
        self.disposition_done = asyncio.Event()
        self.resume_event = asyncio.Event()
        self.current_page = initial_page
        self.page_jump_requested = False
        self.requested_page = initial_page
        self.root = None
        self._status_lbl = None
        self._lead_lbl = None
        self._stats_lbl = None
        self._page_entry = None
        self._thread = threading.Thread(target=self._build, daemon=True)
        self._thread.start()
        time.sleep(0.4)

    def _build(self):
        try:
            self.root = tk.Tk()
            self.root.title("Auto-Dialer Control")
            self.root.geometry("340x350+25+25")
            self.root.attributes("-topmost", True)
            self.root.resizable(False, False)
            self.root.configure(bg="#1E1E2E")

            self._status_lbl = tk.Label(
                self.root,
                text="STARTING...",
                font=("Segoe UI", 10, "bold"),
                fg="#F9E2AF",
                bg="#1E1E2E",
                wraplength=320,
                justify="left"
            )
            self._status_lbl.pack(pady=(8, 2), padx=10, anchor="w")

            self._lead_lbl = tk.Label(
                self.root,
                text="Lead: -",
                font=("Segoe UI", 9),
                fg="#89B4FA",
                bg="#1E1E2E"
            )
            self._lead_lbl.pack(padx=10, anchor="w")

            self._stats_lbl = tk.Label(
                self.root,
                text="Dialed: 0 | Connected: 0 | DNP: 0",
                font=("Segoe UI", 8),
                fg="#BAC2DE",
                bg="#1E1E2E"
            )
            self._stats_lbl.pack(padx=10, anchor="w", pady=(0, 4))

            # Chrome Connection Action Row (Quick Launch & Reconnect)
            chrome_frame = tk.Frame(self.root, bg="#1E1E2E")
            chrome_frame.pack(fill=tk.X, padx=10, pady=(0, 6))

            tk.Button(chrome_frame, text="🚀 Launch Chrome", font=("Segoe UI", 8, "bold"), bg="#89DCEB", fg="#11111B",
                      cursor="hand2", command=self._on_launch_chrome).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 2))

            tk.Button(chrome_frame, text="🔄 Connect", font=("Segoe UI", 8, "bold"), bg="#FAB387", fg="#11111B",
                      cursor="hand2", command=self._on_retry_connect).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(2, 0))

            # Page Navigation Row (Jump to any page anytime)
            page_frame = tk.Frame(self.root, bg="#1E1E2E")
            page_frame.pack(fill=tk.X, padx=10, pady=(0, 6))

            tk.Label(page_frame, text="Page:", font=("Segoe UI", 9, "bold"), fg="#CDD6F4", bg="#1E1E2E").pack(side=tk.LEFT)

            self._page_entry = tk.Entry(page_frame, width=4, font=("Segoe UI", 9, "bold"), justify="center", bg="#313244", fg="#F5E0DC", insertbackground="white")
            self._page_entry.insert(0, str(self.current_page))
            self._page_entry.pack(side=tk.LEFT, padx=(4, 6))

            tk.Button(page_frame, text="Go", font=("Segoe UI", 8, "bold"), bg="#CBA6F7", fg="#11111B",
                      cursor="hand2", width=4, command=self._on_jump_page).pack(side=tk.LEFT, padx=1)

            tk.Button(page_frame, text="◀ Prev", font=("Segoe UI", 8), bg="#45475A", fg="#CDD6F4",
                      cursor="hand2", command=self._on_prev_page).pack(side=tk.LEFT, padx=2)

            tk.Button(page_frame, text="Next ▶", font=("Segoe UI", 8), bg="#45475A", fg="#CDD6F4",
                      cursor="hand2", command=self._on_next_page).pack(side=tk.LEFT, padx=2)

            tk.Button(
                self.root,
                text="📞 Customer Answered",
                font=("Segoe UI", 10, "bold"),
                bg="#A6E3A1",
                fg="#11111B",
                cursor="hand2",
                command=self._on_customer_answered
            ).pack(fill=tk.X, padx=10, pady=2)

            tk.Button(
                self.root,
                text="💾 Disposition Done (Resume)",
                font=("Segoe UI", 9, "bold"),
                bg="#89B4FA",
                fg="#11111B",
                cursor="hand2",
                command=self._on_disposition_done
            ).pack(fill=tk.X, padx=10, pady=2)

            row = tk.Frame(self.root, bg="#1E1E2E")
            row.pack(fill=tk.X, padx=10, pady=4)

            tk.Button(
                row,
                text="⏭ Skip",
                font=("Segoe UI", 9),
                bg="#F38BA8",
                fg="#11111B",
                cursor="hand2",
                command=lambda: self.loop.call_soon_threadsafe(self.skip_lead.set)
            ).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 2))

            tk.Button(
                row,
                text="⏸ Pause",
                font=("Segoe UI", 9),
                bg="#F9E2AF",
                fg="#11111B",
                cursor="hand2",
                command=self._toggle_pause
            ).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

            tk.Button(
                row,
                text="🛑 Stop",
                font=("Segoe UI", 9),
                bg="#585B70",
                fg="#CDD6F4",
                cursor="hand2",
                command=self._stop
            ).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(2, 0))

            self.root.protocol("WM_DELETE_WINDOW", self._stop)
            self.root.mainloop()
        except Exception as e:
            print(f"[GUI] Controller Error: {e}")

    def _on_customer_answered(self):
        self.status("📞 CUSTOMER ANSWERED (AUTO-PAUSED)")
        self.paused = True
        self.loop.call_soon_threadsafe(self.customer_answered.set)

    def _on_disposition_done(self):
        self.paused = False
        self.status("▶ RESUMING DIALER...")
        self.loop.call_soon_threadsafe(self.disposition_done.set)
        self.loop.call_soon_threadsafe(self.resume_event.set)

    def _on_launch_chrome(self):
        self.status("🚀 Launching Google Chrome...")
        threading.Thread(target=auto_launch_chrome, daemon=True).start()

    def _on_retry_connect(self):
        self.status("🔄 Connecting to Chrome on port 9222...")
        self.retry_connect_requested = True

    def _on_jump_page(self):
        try:
            val = int(self._page_entry.get().strip())
            if val >= 1:
                self.requested_page = val
                self.page_jump_requested = True
        except ValueError:
            pass

    def _on_prev_page(self):
        try:
            val = int(self._page_entry.get().strip())
            if val > 1:
                self.requested_page = val - 1
                self.page_jump_requested = True
                self.set_page_display(self.requested_page)
        except ValueError:
            pass

    def _on_next_page(self):
        try:
            val = int(self._page_entry.get().strip())
            self.requested_page = val + 1
            self.page_jump_requested = True
            self.set_page_display(self.requested_page)
        except ValueError:
            pass

    def set_page_display(self, page_num):
        self.current_page = page_num
        if self.root and self._page_entry:
            try:
                self.root.after(0, lambda: self._update_entry(page_num))
            except Exception:
                pass

    def _update_entry(self, page_num):
        try:
            if self._page_entry:
                self._page_entry.delete(0, tk.END)
                self._page_entry.insert(0, str(page_num))
        except Exception:
            pass

    def _toggle_pause(self):
        self.paused = not self.paused
        if not self.paused:
            self.status("▶ RESUMED")
            self.loop.call_soon_threadsafe(self.resume_event.set)
            self.loop.call_soon_threadsafe(self.disposition_done.set)
        else:
            self.status("⏸️ PAUSED")
        if not self.paused:
            self.loop.call_soon_threadsafe(self.resume_event.set)

    def _stop(self):
        self.stopped = True
        self.loop.call_soon_threadsafe(self.skip_lead.set)
        try:
            if self.root:
                self.root.after(0, self.root.quit)
        except Exception:
            pass

    def status(self, text):
        if self.root and self._status_lbl:
            try:
                self.root.after(0, lambda: self._safe_config_label(self._status_lbl, text))
            except Exception:
                pass

    def _safe_config_label(self, lbl, text):
        try:
            lbl.config(text=text)
        except Exception:
            pass

    def lead(self, name):
        if self.root and self._lead_lbl:
            try:
                self.root.after(0, lambda: self._safe_config_label(self._lead_lbl, f"Lead: {name[:30]}"))
            except Exception:
                pass

    def stats(self, dialed, connected, dnp):
        if self.root and self._stats_lbl:
            try:
                txt = f"Dialed: {dialed} | Connected: {connected} | DNP: {dnp}"
                self.root.after(0, lambda: self._safe_config_label(self._stats_lbl, txt))
            except Exception:
                pass


# ============================================================
# MAIN AUTO-DIALER
# ============================================================
class AutoDialer:
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.lsq: Optional[Page] = None
        self.mcube: Optional[Page] = None
        self.mcube_portal: Optional[Page] = None
        self.mcube_pages: list[Page] = []
        self.ctrl: Optional[MiniController] = None
        self.pw = None
        self.dialed = 0
        self.connected = 0
        self.dnp = 0
        self.processed = set()
        self.current_phone = ""

    async def connect(self):
        """Connect to Chrome via CDP and find active pages with resilient auto-retry."""
        while not self.ctrl.stopped:
            if not is_port_open("127.0.0.1", 9222):
                self.ctrl.status("⚠️ WAITING FOR CHROME (PORT 9222)...")
                log("Chrome is not listening on port 9222. Auto-launching Google Chrome...", "INFO")
                # Run auto_launch_chrome in background executor so Tkinter UI does not freeze
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, auto_launch_chrome)

            if is_port_open("127.0.0.1", 9222):
                self.ctrl.status("🔄 CONNECTING TO CHROME CDP...")
                try:
                    if not self.pw:
                        self.pw = await async_playwright().start()
                    self.browser = await self.pw.chromium.connect_over_cdp(CDP_URL)
                    log("Connected to Google Chrome successfully!", "OK")
                    self.ctrl.status("🔍 SEARCHING TABS...")
                    await self.find_pages()
                    return True
                except Exception as e:
                    log(f"CDP connection attempt error: {e}", "WARN")
                    self.ctrl.status("⚠️ RETRYING CHROME CDP CONNECTION...")
            else:
                self.ctrl.status("⚠️ CHROME NOT DETECTED: CLICK '🚀 LAUNCH CHROME'")

            # Wait before re-checking, or wake immediately if user clicked retry
            for _ in range(6):
                if self.ctrl.stopped:
                    return False
                if self.ctrl.retry_connect_requested:
                    self.ctrl.retry_connect_requested = False
                    break
                await asyncio.sleep(0.5)

        return False

    async def find_pages(self):
        """Dynamically detect or refresh LeadSquared and MCUBE pages."""
        self.lsq = None
        self.mcube = None
        self.mcube_portal = None
        self.mcube_pages = []

        if not self.browser or not self.browser.contexts:
            return

        # Prioritize exact Manage Opportunities tab and MCUBE Soft Phone
        for ctx in self.browser.contexts:
            for p in ctx.pages:
                if p.is_closed():
                    continue
                url = p.url.lower()

                # Track ALL MCUBE pages (both Soft Phone and Portal / Dashboard)
                if "mcube" in url:
                    self.mcube_pages.append(p)
                    if "dialer.mcube.com" in url and not self.mcube:
                        self.mcube = p
                        log(f"Found MCUBE Phone tab: {p.url[:60]}", "OK")
                    if "vedantu.mcube.com" in url and not self.mcube_portal:
                        self.mcube_portal = p
                        log(f"Found MCUBE Portal tab: {p.url[:60]}", "OK")

                # LeadSquared Manage Grid or Identity login
                if "opportunitymanagement?ec=12000" in url and not self.lsq:
                    self.lsq = p
                    log(f"Found LeadSquared Grid: {p.url[:60]}", "OK")

        # Fallback for LeadSquared if exact grid URL not found yet
        if not self.lsq:
            for ctx in self.browser.contexts:
                for p in ctx.pages:
                    if p.is_closed():
                        continue
                    url = p.url.lower()
                    if ("opportunitymanagement" in url or "leadsquared.com" in url) and "error" not in url:
                        self.lsq = p
                        log(f"Found LeadSquared page: {p.url[:60]}", "OK")
                        break

        # Fallback for MCUBE if dialer.mcube.com not explicitly matched yet
        if not self.mcube and self.mcube_pages:
            self.mcube = self.mcube_pages[0]
            log(f"Using primary MCUBE tab: {self.mcube.url[:60]}", "OK")

        # Fallback: create LeadSquared page if completely absent
        ctx = self.browser.contexts[0]
        if not self.lsq:
            log(f"Opening LeadSquared tab: {LSQ_MANAGE_URL}", "INFO")
            self.lsq = await ctx.new_page()
            await self.lsq.goto(LSQ_MANAGE_URL)

        # Fallback: create MCUBE page if completely absent
        if not self.mcube:
            log("Opening MCUBE Dialer tab: https://dialer.mcube.com/index.html", "INFO")
            self.mcube = await ctx.new_page()
            await self.mcube.goto("https://dialer.mcube.com/index.html")
            self.mcube_pages.append(self.mcube)

        # Attach auto-dialog accepter for native alerts/confirms
        if self.lsq:
            try:
                self.lsq.on("dialog", lambda dialog: asyncio.create_task(dialog.accept()))
            except Exception:
                pass

    async def ensure_on_grid(self):
        """Ensure self.lsq is logged in and on the Opportunity Management grid."""
        await self.find_pages()

        # Check if LeadSquared requires login
        while not self.ctrl.stopped:
            url = self.lsq.url.lower() if self.lsq else ""
            if "identity.leadsquared.com" in url or "login" in url:
                self.ctrl.status("🔑 PLEASE LOG IN TO LEADSQUARED")
                log("LeadSquared login required. Please enter credentials in Chrome...", "WARN")
                await asyncio.sleep(2)
                await self.find_pages()
                continue
            break

        # Check if MCUBE requires login
        while not self.ctrl.stopped and self.mcube and not self.mcube.is_closed():
            try:
                m_body = (await self.mcube.inner_text("body")).lower()
                if "login" in m_body or "sign in" in m_body:
                    self.ctrl.status("🔑 PLEASE LOG IN TO MCUBE")
                    log("MCUBE login required. Please enter credentials in MCUBE Soft Phone...", "WARN")
                    await asyncio.sleep(2)
                    continue
            except Exception:
                pass
            break

        url = self.lsq.url.lower() if self.lsq else ""

        # If currently on OpportunityDetails, use LeadSquared's native GoBackToSource()
        if "opportunitydetails" in url:
            log("On Details page. Returning to grid via GoBackToSource()...", "INFO")
            try:
                await self.lsq.evaluate("GoBackToSource()")
                await asyncio.sleep(2)
            except Exception:
                await self.lsq.goto(LSQ_MANAGE_URL)

        elif "opportunitymanagement" not in url:
            log(f"Navigating to grid ({LSQ_MANAGE_URL})...", "INFO")
            await self.lsq.goto(LSQ_MANAGE_URL, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(2)

        # Wait for table rows to be present
        try:
            await self.lsq.wait_for_selector("table tbody tr", timeout=15000)
            await asyncio.sleep(1)
        except Exception:
            log("Waiting for grid rows to appear...", "WARN")

    async def get_matching_rows(self):
        """
        Find all table rows matching target stages.
        Extracts ONLY the Opportunity link ('a[href*='OpportunityDetails']').
        """
        rows = await self.lsq.locator("table tbody tr").all()
        results = []

        for row in rows:
            try:
                text = await row.inner_text()

                # Skip if row text explicitly displays an excluded sub-stage
                if any(exc.lower() in text.lower() for exc in EXCLUDE_SUB_STAGES):
                    continue

                matched_stage = None
                for stage in TARGET_STAGES:
                    if stage.lower() in text.lower():
                        matched_stage = stage
                        break

                if not matched_stage:
                    continue

                # Locate the OpportunityDetails link in this row
                opp_candidates = row.locator("a[href*='OpportunityDetails'], a[href*='opportunityId']")
                if await opp_candidates.count() > 0:
                    opp_link = opp_candidates.first
                    link_text = (await opp_link.inner_text()).strip()
                    href = await opp_link.get_attribute("href") or ""

                    if link_text and not link_text.startswith("+91") and "[no name]" not in link_text.lower():
                        key = f"{link_text}_{href}"
                        if key not in self.processed:
                            results.append({
                                "name": link_text,
                                "stage": matched_stage,
                                "key": key,
                                "href": href,
                                "locator": opp_link
                            })

            except Exception:
                continue

        return results

    async def click_opportunity(self, lead):
        """Click the Opportunity Name link to open Opportunity Details."""
        log(f"Opening Opportunity: {lead['name']} ({lead['stage']})", "CALL")
        self.ctrl.lead(f"{lead['name']} ({lead['stage']})")
        self.ctrl.status("📂 OPENING OPPORTUNITY...")

        try:
            # 1. Click via locator
            clicked = False
            if lead.get("locator"):
                try:
                    await lead["locator"].click(timeout=3000)
                    clicked = True
                except Exception:
                    pass

            # 2. Fallback: by href or text
            if not clicked:
                loc = self.lsq.locator(f"table tbody tr a[href*='{lead['href']}']").first
                if await loc.is_visible(timeout=2000):
                    await loc.click()
                    clicked = True

            if not clicked:
                loc = self.lsq.locator("table tbody tr a[href*='OpportunityDetails']", has_text=lead["name"]).first
                await loc.click(timeout=5000)

            await asyncio.sleep(2)
            await self.lsq.wait_for_load_state("domcontentloaded", timeout=15000)
            await asyncio.sleep(1)
            return True
        except Exception as e:
            log(f"Error opening opportunity: {e}", "ERR")
            return False

    async def get_lead_sub_stages(self) -> dict:
        """
        Extract Stage, Sub Stage, and Super Sub Stage from the Opportunity Details page.
        """
        try:
            return await self.lsq.evaluate("""() => {
                let stage = '';
                let subStage = '';
                let superSubStage = '';

                // 1. Look for table rows where first cell matches Stage, Sub Stage or Super Sub Stage
                const trs = Array.from(document.querySelectorAll('tr'));
                for (const tr of trs) {
                    const cells = Array.from(tr.querySelectorAll('td, th'));
                    if (cells.length >= 2) {
                        const lbl = cells[0].innerText.trim();
                        if (/^(Opportunity\\s*)?Stage$/i.test(lbl)) {
                            stage = cells[1].innerText.trim();
                        } else if (/^Sub\\s*Stage$/i.test(lbl)) {
                            subStage = cells[1].innerText.trim();
                        } else if (/^Super\\s*Sub\\s*Stage$/i.test(lbl)) {
                            superSubStage = cells[1].innerText.trim();
                        }
                    }
                }

                // 2. Look for dt/dd or label/value pairs
                if (!subStage || !superSubStage || !stage) {
                    const labels = Array.from(document.querySelectorAll('label, dt, .label, .field-label, span, div'));
                    for (const l of labels) {
                        const txt = l.innerText.trim();
                        if (/^(Opportunity\\s*)?Stage$/i.test(txt) && !stage) {
                            const next = l.nextElementSibling;
                            if (next) stage = next.innerText.trim();
                        }
                        if (/^Sub\\s*Stage$/i.test(txt) && !subStage) {
                            const next = l.nextElementSibling;
                            if (next) subStage = next.innerText.trim();
                        }
                        if (/^Super\\s*Sub\\s*Stage$/i.test(txt) && !superSubStage) {
                            const next = l.nextElementSibling;
                            if (next) superSubStage = next.innerText.trim();
                        }
                    }
                }

                // 3. Fallback: Parse body lines
                if (!subStage || !superSubStage || !stage) {
                    const lines = (document.body.innerText || '').split('\\n');
                    for (let i = 0; i < lines.length; i++) {
                        const line = lines[i].trim();
                        if (/^(Opportunity\\s*)?Stage$/i.test(line) && i + 1 < lines.length && !stage) {
                            stage = lines[i + 1].trim();
                        }
                        if (/^Sub\\s*Stage$/i.test(line) && i + 1 < lines.length && !subStage) {
                            subStage = lines[i + 1].trim();
                        }
                        if (/^Super\\s*Sub\\s*Stage$/i.test(line) && i + 1 < lines.length && !superSubStage) {
                            superSubStage = lines[i + 1].trim();
                        }
                    }
                }

                return { stage: stage, sub_stage: subStage, super_sub_stage: superSubStage };
            }""")
        except Exception:
            return {"stage": "", "sub_stage": "", "super_sub_stage": ""}

    async def confirm_yes(self):
        """
        Wait for the LeadSquared confirmation dialog to appear and click 'Yes'.
        Uses multiple locator strategies with force-click and direct JavaScript evaluation.
        """
        log("Waiting for 'Yes' confirmation dialog...", "INFO")
        self.ctrl.status("👉 CLICKING 'YES'...")

        yes_selectors = [
            "button:has-text('Yes')",
            "a:has-text('Yes')",
            "input[value='Yes']",
            "button:has-text('YES')",
            "a:has-text('YES')",
            ".modal-footer button:has-text('Yes')",
            ".modal-footer a:has-text('Yes')",
            ".modal button:has-text('Yes')",
            ".modal a:has-text('Yes')",
            ".modal-dialog button:has-text('Yes')",
            ".modal-dialog a:has-text('Yes')",
            "button[data-bb-handler='confirm']",
            "button[data-bb-handler='main']",
            ".bootbox button:has-text('Yes')",
            ".ui-dialog-buttonset button:has-text('Yes')",
            ".modal.in .btn-primary",
            ".modal.show .btn-primary",
            ".modal-dialog .btn-primary",
            ".modal-footer .btn-primary"
        ]

        start_wait = time.time()
        while time.time() - start_wait < 6.0:
            # 1. Try JavaScript evaluation first (instant, bypasses animation / overlays)
            try:
                js_clicked = await self.lsq.evaluate("""() => {
                    const elements = Array.from(document.querySelectorAll('button, a, input[type="button"], input[type="submit"]'));
                    for (const el of elements) {
                        const txt = (el.innerText || el.value || '').trim();
                        if (/^yes\\b/i.test(txt) && el.offsetParent !== null) {
                            el.click();
                            return txt;
                        }
                    }
                    return null;
                }""")
                if js_clicked:
                    log(f"Successfully clicked '{js_clicked}' via JavaScript evaluation!", "OK")
                    await asyncio.sleep(1)
                    return True
            except Exception:
                pass

            # 2. Try Playwright locators on main page
            for sel in yes_selectors:
                try:
                    btn = self.lsq.locator(sel).first
                    if await btn.is_visible(timeout=200):
                        txt = (await btn.inner_text()).strip()
                        if "no" in txt.lower() or "cancel" in txt.lower():
                            continue
                        try:
                            await btn.click(timeout=1000)
                        except Exception:
                            await btn.click(force=True, timeout=1000)
                        log(f"Successfully clicked '{txt}' confirmation button via '{sel}'!", "OK")
                        await asyncio.sleep(1)
                        return True
                except Exception:
                    continue

            # 3. Check inside any iframes
            for frame in self.lsq.frames:
                if frame == self.lsq.main_frame:
                    continue
                try:
                    frame_clicked = await frame.evaluate("""() => {
                        const elements = Array.from(document.querySelectorAll('button, a, input[type="button"], input[type="submit"]'));
                        for (const el of elements) {
                            const txt = (el.innerText || el.value || '').trim();
                            if (/^yes\\b/i.test(txt) && el.offsetParent !== null) {
                                el.click();
                                return txt;
                            }
                        }
                        return null;
                    }""")
                    if frame_clicked:
                        log(f"Successfully clicked '{frame_clicked}' in iframe!", "OK")
                        await asyncio.sleep(1)
                        return True
                except Exception:
                    pass

            await asyncio.sleep(0.2)

        log("Notice: 'Yes' confirmation button was not detected within 6s", "WARN")
        return False

    async def dismiss_alerts(self):
        """Auto-dismiss any notification or alert dialogs that appear after Yes."""
        try:
            await self.lsq.evaluate("""() => {
                const buttons = Array.from(document.querySelectorAll('button, a, input[type="button"]'));
                for (const b of buttons) {
                    const txt = (b.innerText || b.value || '').trim();
                    if (/^(ok|okay|close|dismiss)\\b/i.test(txt) && b.offsetParent !== null) {
                        b.click();
                        return;
                    }
                }
            }""")
        except Exception:
            pass

    async def find_and_click_phone(self):
        """
        On Opportunity Details:
        Locate and click the EXACT click-to-call link:
        'a[onclick*='onLeadDetailsNumberClick']'
        Then automatically clicks 'Yes' to initiate the call.
        """
        self.ctrl.status("📱 CLICKING PHONE NUMBER...")
        await asyncio.sleep(1.5)

        # LeadSquared click-to-call link uses onLeadDetailsNumberClick()
        phone_link = self.lsq.locator("a[onclick*='onLeadDetailsNumberClick']").first

        cnt = await phone_link.count()
        if cnt == 0:
            # Fallback: find any link with '+91' that is NOT LeadDetails
            phone_link = self.lsq.locator("a:has-text('+91'):not([href*='LeadDetails'])").first
            cnt = await phone_link.count()

        if cnt == 0:
            log("No click-to-call phone link found on Details page", "WARN")
            return False

        phone_text = (await phone_link.inner_text()).strip()
        self.current_phone = phone_text
        log(f"Found Click-to-Call Phone: {phone_text}", "OK")

        await phone_link.scroll_into_view_if_needed()
        await asyncio.sleep(0.5)
        await phone_link.click()
        log("Clicked phone link! Waiting to click 'Yes'...", "INFO")

        # Explicitly confirm call by clicking 'Yes'
        await self.confirm_yes()

        # Dismiss any subsequent alert dialog
        await asyncio.sleep(0.5)
        await self.dismiss_alerts()

        return True

    async def check_call_status(self) -> Optional[str]:
        """
        Check across MCUBE Landing Page (https://vedantu.mcube.com/#/Home/landingpage),
        Asterisk Confbridge channels, and the live call log table:
        Returns:
            "ANSWER" -> Customer answered / connected (trigger auto-pause)
            "BUSY"   -> Customer is busy / rejected / failed / DNP (do not pause, mark DNP)
            None     -> Still ringing / calling in progress
        """
        # 1. MiniController manual button ('Customer Answered')
        if self.ctrl and self.ctrl.customer_answered.is_set():
            log("Customer answer confirmed via Controller button!", "OK")
            return "ANSWER"

        # 2. Check MCUBE Landing Page (https://vedantu.mcube.com/#/Home/landingpage)
        # Analyzes live .call-notification widget ('On Call', 'Calling', 'DNP', etc.)
        # and non-DNP Disposition Form popup.
        for p in self.mcube_pages:
            if p.is_closed() or "vedantu.mcube.com" not in p.url.lower():
                continue
            try:
                portal_state = await p.evaluate("""() => {
                    try {
                        // A. Check .call-notification widget
                        let notif = document.querySelector('.call-notification');
                        if (notif) {
                            let text = (notif.innerText || '').toUpperCase();
                            let cls = (notif.className || '').toLowerCase();

                            // Explicit DNP or Busy or Failed or Disconnected
                            if (text.includes('DNP') || text.includes('BUSY') || text.includes('FAILED') || 
                                text.includes('NO ANSWER') || text.includes('CANCEL') || text.includes('AGENT BUSY')) {
                                return 'BUSY';
                            }

                            // Explicit Customer Answer / Connected:
                            // MCUBE Angular template displays "On Call" when dialstatus == "ANSWER",
                            // or adds "disposition-width" to the .call-notification class.
                            if (text.includes('ON CALL') || text.includes('ANSWER') || cls.includes('disposition-width')) {
                                return 'ANSWER';
                            }
                        }

                        // B. Check MCUBE Disposition Popup / Dialog / Overlay (.cdk-overlay-pane, .disposition-width, etc.)
                        let overlay = document.querySelector('.cdk-overlay-pane, .disposition-width, [class*="disposition-width"]');
                        if (overlay) {
                            let text = (overlay.innerText || '').toUpperCase();
                            if (text.includes('DISPOSITION FORM') || text.includes('DISPOSITION')) {
                                if (text.includes('DNP') || text.includes('BUSY') || text.includes('FAILED') || text.includes('CANCEL')) {
                                    return 'BUSY';
                                }
                                // Non-DNP Disposition Form popup -> Customer picked up, call is connected!
                                return 'ANSWER';
                            }
                        }
                    } catch(e) {}
                    return null;
                }""")
                if portal_state == "ANSWER":
                    log(f"MCUBE Landing Page ({p.url[:40]}): Call is CONNECTED ('On Call' / Non-DNP Disposition Form detected)!", "OK")
                    return "ANSWER"
                elif portal_state == "BUSY":
                    log(f"MCUBE Landing Page ({p.url[:40]}): Call status is 'DNP' / 'BUSY'!", "WARN")
                    return "BUSY"
            except Exception:
                pass

        # 3. Check Asterisk Confbridge channels on dialer.mcube.com
        # Leg-A has ConfbridgeChannels.length == 1; Leg-B (customer) joining makes length >= 2
        if self.mcube and not self.mcube.is_closed():
            try:
                conf_state = await self.mcube.evaluate("""() => {
                    try {
                        if (typeof userAgent !== 'undefined' && userAgent && userAgent.sessions) {
                            for (let id in userAgent.sessions) {
                                let s = userAgent.sessions[id];
                                if (s && s.data) {
                                    let chans = s.data.ConfbridgeChannels || [];
                                    if (chans.length >= 2) return 'ANSWER';
                                    let events = s.data.ConfbridgeEvents || [];
                                    if (events.length >= 2) return 'ANSWER';
                                }
                            }
                        }
                    } catch(e) {}
                    return null;
                }""")
                if conf_state == "ANSWER":
                    log("MCUBE Softphone: Customer bridged into conference (ConfbridgeChannels >= 2)!", "OK")
                    return "ANSWER"
            except Exception:
                pass

        # 4. Check Row 0 (most recent call) on vedantu.mcube.com live table
        phone_tail = re.sub(r'\D', '', self.current_phone)[-4:] if self.current_phone else ""
        for p in self.mcube_pages:
            if p.is_closed() or "vedantu.mcube.com" not in p.url.lower():
                continue
            try:
                row_status = await p.evaluate("""(phoneTail) => {
                    try {
                        let row = document.querySelector('table tbody tr');
                        if (!row) return null;
                        let cells = Array.from(row.querySelectorAll('td')).map(c => c.innerText.trim());
                        if (cells.length < 8) return null;
                        let cust = cells[1] || '';
                        let st = (cells[7] || '').toUpperCase();
                        if (!phoneTail || cust.includes(phoneTail)) {
                            if (st === 'ANSWER' || st === 'ANSWERED') {
                                return 'ANSWER';
                            }
                            if (st.includes('BUSY') || st === 'NO ANSWER' || st === 'DNP' || st === 'CANCEL') {
                                return 'BUSY';
                            }
                        }
                    } catch(e) {}
                    return null;
                }""", phone_tail)
                if row_status == "ANSWER":
                    log(f"MCUBE Live Call Log ({p.url[:40]}): Current call status is 'ANSWER'!", "OK")
                    return "ANSWER"
                elif row_status == "BUSY":
                    log(f"MCUBE Live Call Log ({p.url[:40]}): Current call status is 'BUSY'!", "WARN")
                    return "BUSY"
            except Exception:
                pass

        return None

    async def monitor_call(self):
        """
        Monitor MCUBE telephony state with Non-DNP Disposition Form & 'On Call' Detection:
        1. MCUBE Landing Page (https://vedantu.mcube.com/#/Home/landingpage):
           - Detects 'On Call' status / widened disposition-width panel -> AUTO-PAUSES!
           - Detects Non-DNP Disposition Form popup -> AUTO-PAUSES!
           - Recognizes DNP / BUSY status -> marks DNP and advances!
        2. Checks Asterisk Confbridge channels (length >= 2 = customer bridged).
        3. Checks Live MCUBE Call Log Row 0 (ANSWER vs BUSY).
        4. MiniController manual button ('Customer Answered') for 1-click override.
        """
        self.ctrl.status("📞 RINGING CUSTOMER...")
        self.ctrl.customer_answered.clear()
        self.ctrl.skip_lead.clear()

        await self.find_pages()

        start = time.time()
        saw_in_progress = False

        while time.time() - start < RING_TIMEOUT:
            elapsed = int(time.time() - start)
            remaining = int(RING_TIMEOUT - elapsed)
            self.ctrl.status(f"📞 RINGING CUSTOMER... ({remaining}s)")

            # Auto-click any remaining alert dialogs
            await self.dismiss_alerts()

            # 1. Manual override from MiniController
            if self.ctrl.customer_answered.is_set():
                log("Customer Answer confirmed via Controller!", "OK")
                return "CONNECTED"

            if self.ctrl.skip_lead.is_set():
                log("Manual Skip clicked", "WARN")
                return "SKIPPED"

            # 2. Check MCUBE call status (Landing page disposition popup, Confbridge & Row 0)
            status = await self.check_call_status()
            if status == "ANSWER":
                log("📞 CALL STATUS: ANSWER CONFIRMED (MCUBE Disposition / On Call pattern) — AUTO-PAUSED!", "OK")
                return "CONNECTED"
            elif status == "BUSY":
                log("MCUBE: Customer is BUSY / DNP (confirmed via call status) — moving to next lead", "WARN")
                return "DNP"

            # 3. Check MCUBE popup status for ringing vs disconnect
            if self.mcube and not self.mcube.is_closed():
                try:
                    body = await self.mcube.inner_text("body")
                    lower = body.lower()

                    if any(k in lower for k in ["call in progress", "calling", "ringing"]):
                        saw_in_progress = True

                    # Check for Call ended / Disconnected
                    if "call ended" in lower or "disconnected" in lower:
                        await asyncio.sleep(0.5)
                        status_final = await self.check_call_status()
                        if status_final == "ANSWER":
                            return "CONNECTED"
                        log("MCUBE: Call ended without customer answer (DNP/BUSY)", "WARN")
                        return "DNP"

                    # If ringing stopped after at least 6s without customer pickup
                    if saw_in_progress and not any(k in lower for k in ["call in progress", "calling", "ringing"]) and elapsed > 6:
                        await asyncio.sleep(0.8)
                        status_final = await self.check_call_status()
                        if status_final == "ANSWER":
                            return "CONNECTED"
                        log("MCUBE: Outgoing ring stopped (DNP/BUSY)", "WARN")
                        return "DNP"

                except Exception:
                    pass

            await asyncio.sleep(0.3)

        # Final check on timeout
        status_final = await self.check_call_status()
        if status_final == "ANSWER":
            return "CONNECTED"

        log(f"Ring timeout ({RING_TIMEOUT}s) - Customer did not pick up", "WARN")
        return "TIMEOUT"

    async def return_to_grid(self):
        """
        Return to Opportunity Management grid via GoBackToSource().
        """
        log("Returning to grid via GoBackToSource()...", "INFO")
        self.ctrl.status("🔙 RETURNING TO GRID...")

        try:
            await self.lsq.evaluate("GoBackToSource()")
            await asyncio.sleep(2)
        except Exception:
            # Fallback: click back button or goto URL
            try:
                back_btn = self.lsq.locator("a[onclick*='GoBackToSource'], a:has-text('Back')").first
                if await back_btn.is_visible(timeout=1500):
                    await back_btn.click()
                    await asyncio.sleep(2)
                else:
                    await self.lsq.goto(LSQ_MANAGE_URL)
            except Exception:
                await self.lsq.goto(LSQ_MANAGE_URL)

        # Wait for grid rows to appear
        try:
            await self.lsq.wait_for_selector("table tbody tr", timeout=12000)
            log("Successfully returned to Opportunity grid!", "OK")
        except Exception:
            pass

    async def wait_for_disposition(self):
        """
        Auto-pause on connected call and wait until disposition is sent or agent resumes.
        Will NOT proceed until agent finishes speaking and disposition is saved.
        """
        self.ctrl.paused = True
        self.ctrl.status("🗣️ CALL CONNECTED — AUTO-PAUSED")
        self.ctrl.disposition_done.clear()
        self.ctrl.resume_event.clear()

        log("=" * 65, "OK")
        log("📞 CUSTOMER CONNECTED — DIALER AUTO-PAUSED", "OK")
        log("👉 Lead Details open. Speak with customer and save disposition in LeadSquared.", "INFO")
        log("👉 Auto-dialer will remain PAUSED until disposition is saved or 'Disposition Done' is clicked.", "INFO")
        log("=" * 65, "OK")

        disposition_saved = asyncio.Event()

        def on_lsq_response(resp):
            try:
                if resp.status in (200, 201) and resp.request.method == "POST":
                    url = resp.url.lower()
                    if any(k in url for k in ["save", "createactivity", "updateopportunity", "postactivity", "processform", "customaction"]):
                        if not any(k in url for k in ["track", "ping", "notification", "keepalive", "log", "analytics", "presence"]):
                            log(f"LeadSquared disposition save detected: {resp.url[:70]}", "OK")
                            disposition_saved.set()
            except Exception:
                pass

        def on_mcube_response(resp):
            try:
                if resp.status in (200, 201) and resp.request.method in ("POST", "PUT"):
                    url = resp.url.lower()
                    if any(k in url for k in ["disposition", "savedisposition", "calldisposition", "updatedisposition"]):
                        log(f"MCUBE disposition save detected: {resp.url[:70]}", "OK")
                        disposition_saved.set()
            except Exception:
                pass

        if self.lsq:
            try:
                self.lsq.on("response", on_lsq_response)
            except Exception:
                pass

        for p in self.mcube_pages:
            try:
                if not p.is_closed():
                    p.on("response", on_mcube_response)
            except Exception:
                pass

        try:
            # Stay paused until disposition POST is caught OR user clicks "Disposition Done"
            while not self.ctrl.disposition_done.is_set() and not disposition_saved.is_set() and not self.ctrl.stopped:
                if not self.ctrl.paused:
                    break
                await asyncio.sleep(0.4)
        finally:
            if self.lsq:
                try:
                    self.lsq.remove_listener("response", on_lsq_response)
                except Exception:
                    pass
            for p in self.mcube_pages:
                try:
                    if not p.is_closed():
                        p.remove_listener("response", on_mcube_response)
                except Exception:
                    pass

        self.ctrl.paused = False
        log("✅ Disposition saved! Returning to grid for next lead...", "OK")
        await asyncio.sleep(DELAY_AFTER_CONNECTED)

    async def get_current_grid_page(self) -> int:
        """Detect current active page number in the LeadSquared grid pagination."""
        try:
            val = await self.lsq.evaluate("""() => {
                const active = document.querySelector('li.active, .pagination .active, .page-item.active, [class*="pagination"] [class*="active"], [class*="pagination"] [class*="selected"]');
                if (active) {
                    const txt = active.innerText.trim();
                    const num = parseInt(txt, 10);
                    if (!isNaN(num)) return num;
                }
                const pageInput = document.querySelector('input.ui-pg-input, input[id*="pager"]');
                if (pageInput && pageInput.value) {
                    const num = parseInt(pageInput.value, 10);
                    if (!isNaN(num)) return num;
                }
                return 1;
            }""")
            return int(val) if val else 1
        except Exception:
            return 1

    async def go_to_grid_page(self, target_page: int) -> bool:
        """Navigate to a specific page number in the grid pagination."""
        current = await self.get_current_grid_page()
        if current == target_page:
            return True

        log(f"Grid is on Page {current}. Navigating to Page {target_page}...", "INFO")
        self.ctrl.status(f"📄 GOING TO PAGE {target_page}...")

        # 1. Try clicking the exact page number button
        try:
            clicked = await self.lsq.evaluate("""(target) => {
                const links = Array.from(document.querySelectorAll('.pagination a, .pagination button, [class*="pager"] a, [class*="pager"] button, [class*="pagination"] *'));
                for (const l of links) {
                    if (l.innerText.trim() === String(target) && l.offsetParent !== null) {
                        l.click();
                        return true;
                    }
                }
                return false;
            }""", target_page)
            if clicked:
                await asyncio.sleep(2)
                await self.lsq.wait_for_selector("table tbody tr", timeout=10000)
                log(f"Navigated to Page {target_page} via page number button!", "OK")
                return True
        except Exception:
            pass

        # 2. Advance page by page if direct click failed
        while current < target_page:
            success = await self.click_next_page()
            if not success:
                break
            await asyncio.sleep(2)
            new_page = await self.get_current_grid_page()
            if new_page <= current:
                break
            current = new_page

        return current == target_page

    async def click_next_page(self):
        """Click next page in grid pagination (supporting icons, next siblings, and text arrows)."""
        log("Advancing to next grid page...", "INFO")
        self.ctrl.status("📄 NEXT PAGE...")

        # Strategy 1: JavaScript evaluation targeting next arrow, next sibling, or icon
        try:
            result = await self.lsq.evaluate("""() => {
                // 1. Next button by selector
                const nextSelectors = [
                    'li.next:not(.disabled) a',
                    'li.next:not(.disabled) button',
                    'a[title*="Next" i]:not(.disabled)',
                    'button[title*="Next" i]:not(.disabled)',
                    'a[aria-label*="Next" i]',
                    'button[aria-label*="Next" i]',
                    '.pagination a:has(.fa-angle-right)',
                    '.pagination a:has(.fa-chevron-right)',
                    '.pagination button:has(.fa-angle-right)',
                    '.pagination button:has(.fa-chevron-right)',
                    'td[id*="next"]:not(.ui-state-disabled)'
                ];
                for (const sel of nextSelectors) {
                    try {
                        const el = document.querySelector(sel);
                        if (el && el.offsetParent !== null) {
                            el.click();
                            return { success: true, method: sel };
                        }
                    } catch (e) {}
                }

                // 2. Next sibling of active page in pagination
                const active = document.querySelector('li.active, .pagination .active, .page-item.active, [class*="pagination"] [class*="active"]');
                if (active) {
                    let next = active.nextElementSibling;
                    while (next) {
                        if (next.classList.contains('disabled')) return { success: false, reason: 'disabled' };
                        const clickable = next.querySelector('a, button') || next;
                        if (clickable && clickable.click) {
                            clickable.click();
                            return { success: true, method: 'next_sibling', text: clickable.innerText };
                        }
                        next = next.nextElementSibling;
                    }
                }

                // 3. Any element with text '>', '»', '›', or 'Next'
                const allLinks = Array.from(document.querySelectorAll('.pagination a, .pagination button, [class*="pager"] a, [class*="pager"] button, tfoot a, tfoot button'));
                for (const l of allLinks) {
                    const txt = l.innerText.trim();
                    if ((txt === '>' || txt === '»' || txt === '›' || txt.toLowerCase() === 'next') && l.offsetParent !== null) {
                        if (l.parentElement && l.parentElement.classList.contains('disabled')) {
                            return { success: false, reason: 'disabled' };
                        }
                        l.click();
                        return { success: true, method: 'text_arrow', text: txt };
                    }
                }

                return { success: false, reason: 'not_found' };
            }""")

            if result and result.get("success"):
                log(f"Clicked Next Page ({result.get('method')} {result.get('text', '')})", "OK")
                await asyncio.sleep(2)
                try:
                    await self.lsq.wait_for_selector("table tbody tr", timeout=10000)
                except Exception:
                    pass
                return True
            elif result and result.get("reason") == "disabled":
                log("Next page button is disabled - reached end of grid", "WARN")
                return False
        except Exception as e:
            log(f"JS pagination click warning: {e}", "WARN")

        # Strategy 2: Playwright locators fallback
        locators = [
            "a:has(.fa-angle-right)",
            "button:has(.fa-angle-right)",
            "a:has(.fa-chevron-right)",
            "button:has(.fa-chevron-right)",
            "a[title*='Next']",
            "button[title*='Next']",
            "li.next:not(.disabled) a",
            "a:has-text('>')",
            "a:has-text('›')",
            "a:has-text('»')"
        ]
        for sel in locators:
            try:
                btn = self.lsq.locator(sel).first
                if await btn.is_visible(timeout=1000):
                    parent_cls = await btn.evaluate("el => el.parentElement ? el.parentElement.className : ''")
                    if "disabled" in parent_cls.lower():
                        return False
                    await btn.click()
                    await asyncio.sleep(2)
                    try:
                        await self.lsq.wait_for_selector("table tbody tr", timeout=10000)
                    except Exception:
                        pass
                    log(f"Clicked Next Page via locator '{sel}'", "OK")
                    return True
            except Exception:
                continue

        return False

    def save_session_state(self, page_num):
        """Save current page state so dialer can resume seamlessly after restarting."""
        try:
            with open(STATE_PATH, "w", encoding="utf-8") as f:
                json.dump({"last_page": page_num, "updated_at": ts()}, f, indent=2)
        except Exception:
            pass

    def load_saved_page(self):
        """Load last active page from session_state.json if available."""
        if os.path.exists(STATE_PATH):
            try:
                with open(STATE_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return int(data.get("last_page", 1))
            except Exception:
                pass
        return 1

    async def run(self):
        loop = asyncio.get_event_loop()

        # Priority: CLI argument > config.json > saved session state > Page 1
        saved_page = self.load_saved_page()
        start_page = START_PAGE if START_PAGE > 1 else saved_page
        if start_page < 1:
            start_page = 1

        self.ctrl = MiniController(loop, initial_page=start_page)

        if not await self.connect():
            self.ctrl._stop()
            return

        self.ctrl.status("✅ READY")
        log("=" * 65, "INFO")
        log(f"Auto-Dialer Active | URL: {LSQ_MANAGE_URL}", "OK")
        log(f"Starting at Page: {start_page} | Timeout: {RING_TIMEOUT}s", "INFO")
        log(f"(Change page anytime via Controller or edit 'start_page' in config.json)", "INFO")
        log("=" * 65, "INFO")

        current_grid_page = start_page
        self.save_session_state(current_grid_page)

        try:
            while not self.ctrl.stopped:
                # Handle user jumping to a different page via controller widget
                if self.ctrl.page_jump_requested:
                    target = self.ctrl.requested_page
                    self.ctrl.page_jump_requested = False
                    log(f"Page jump requested by user: Navigating to Page {target}...", "CALL")
                    self.ctrl.status(f"📄 JUMPING TO PAGE {target}...")
                    current_grid_page = target
                    await self.go_to_grid_page(target)
                    self.ctrl.set_page_display(current_grid_page)
                    self.save_session_state(current_grid_page)
                    await asyncio.sleep(1)

                # Handle pause
                if self.ctrl.paused:
                    self.ctrl.status("⏸️ PAUSED")
                    log("Auto-Dialer paused. Click Pause again to resume.", "WARN")
                    self.ctrl.resume_event.clear()
                    await self.ctrl.resume_event.wait()
                    self.ctrl.resume_event.clear()
                    continue

                # 1. Ensure we are on the grid
                self.ctrl.status(f"🔍 SCANNING PAGE {current_grid_page}...")
                await self.ensure_on_grid()

                # If returning to grid reset back to page 1, re-navigate to our active page
                if current_grid_page > 1:
                    page_now = await self.get_current_grid_page()
                    if page_now != current_grid_page:
                        await self.go_to_grid_page(current_grid_page)

                self.ctrl.set_page_display(current_grid_page)
                self.save_session_state(current_grid_page)

                # 2. Get matching leads on current page
                leads = await self.get_matching_rows()
                log(f"[Page {current_grid_page}] Found {len(leads)} unprocessed leads", "INFO")

                # If no leads remain on this page, advance to the next page!
                if not leads:
                    self.ctrl.status(f"📄 ADVANCING FROM PAGE {current_grid_page}...")
                    log(f"Finished leads on Page {current_grid_page}. Moving to Page {current_grid_page + 1}...", "INFO")
                    has_next = await self.click_next_page()
                    if has_next:
                        current_grid_page += 1
                        log(f"Successfully arrived at Page {current_grid_page}!", "OK")
                        self.ctrl.status(f"📄 PAGE {current_grid_page}")
                        self.ctrl.set_page_display(current_grid_page)
                        self.save_session_state(current_grid_page)
                        await asyncio.sleep(1)
                        continue
                    else:
                        self.ctrl.status("⏳ NO MORE LEADS - WAITING 10s")
                        log(f"Reached final grid page (Page {current_grid_page}). Waiting 10s before looping from Page 1...", "WARN")
                        await asyncio.sleep(10)
                        current_grid_page = 1
                        await self.go_to_grid_page(1)
                        self.ctrl.set_page_display(1)
                        self.save_session_state(1)
                        self.processed.clear()
                        continue

                # 3. Process the next lead
                lead = leads[0]
                self.processed.add(lead["key"])

                # Click the Opportunity link
                if not await self.click_opportunity(lead):
                    continue

                # Check Stage, Sub Stage & Super Sub Stage before calling (exclude Demo Done, Wave Form not filled, Language Barrier, Invalid Lead, etc.)
                stages = await self.get_lead_sub_stages()
                stg = stages.get("stage", "").strip() or lead.get("stage", "").strip()
                sub = stages.get("sub_stage", "").strip()
                super_sub = stages.get("super_sub_stage", "").strip()
                if stg or sub or super_sub:
                    log(f"Lead Stage: '{stg}' | Sub Stage: '{sub}' | Super Sub Stage: '{super_sub}'", "INFO")

                should_skip = False
                skip_reason = ""
                for exc in EXCLUDE_SUB_STAGES:
                    exc_lower = exc.lower()
                    if stg and exc_lower in stg.lower():
                        should_skip = True
                        skip_reason = f"Stage is '{stg}' matches excluded '{exc}'"
                        break
                    if sub and exc_lower in sub.lower():
                        should_skip = True
                        skip_reason = f"Sub Stage is '{sub}' matches excluded '{exc}'"
                        break
                    if super_sub and exc_lower in super_sub.lower():
                        should_skip = True
                        skip_reason = f"Super Sub Stage is '{super_sub}' matches excluded '{exc}'"
                        break

                if should_skip:
                    log(f"🚫 SKIPPING LEAD ({lead['name']}): {skip_reason}", "WARN")
                    self.ctrl.status(f"🚫 SKIPPED ({sub or super_sub or stg})")
                    await asyncio.sleep(1)
                    await self.return_to_grid()
                    continue

                # 4. Click the phone number & confirm
                if not await self.find_and_click_phone():
                    log("Skipping lead - phone link unavailable", "WARN")
                    self.dnp += 1
                    self.ctrl.stats(self.dialed, self.connected, self.dnp)
                    await self.return_to_grid()
                    continue

                self.dialed += 1
                self.ctrl.stats(self.dialed, self.connected, self.dnp)

                # 5. Monitor call on MCUBE
                await asyncio.sleep(1)
                result = await self.monitor_call()

                # 6. Handle Call Result
                if result == "CONNECTED":
                    log("=" * 65, "OK")
                    log(f"📞 CALL STATUS: ANSWER — AUTO-PAUSED ON LEAD: {lead['name']}", "OK")
                    log("👉 Auto-dialer paused. Talk to lead and save disposition in LeadSquared.", "INFO")
                    log("=" * 65, "OK")
                    self.connected += 1
                    self.ctrl.stats(self.dialed, self.connected, self.dnp)
                    play_connected_chime()
                    # Auto-pause dialer from advancing to the next lead and calling
                    await self.wait_for_disposition()
                    await self.return_to_grid()

                elif result in ("DNP", "TIMEOUT"):
                    log(f"CALL {result}: {lead['name']}", "WARN")
                    self.dnp += 1
                    self.ctrl.stats(self.dialed, self.connected, self.dnp)
                    self.ctrl.status(f"❌ {result}")
                    await asyncio.sleep(DELAY_AFTER_DNP)
                    await self.return_to_grid()

                elif result == "SKIPPED":
                    log(f"LEAD SKIPPED: {lead['name']}", "WARN")
                    await self.return_to_grid()

                await asyncio.sleep(1)

        except Exception as e:
            log(f"Execution Error: {e}", "ERR")
            import traceback
            traceback.print_exc()
        finally:
            log("=" * 65, "INFO")
            log(f"Summary: Dialed={self.dialed} | Connected={self.connected} | DNP={self.dnp}", "OK")
            log("=" * 65, "INFO")
            if self.pw:
                try:
                    await self.pw.stop()
                except Exception:
                    pass


def show_fatal_error(title, msg):
    try:
        if sys.platform == "win32":
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, str(msg), str(title), 0x10)
            return
    except Exception:
        pass
    try:
        import tkinter.messagebox as mb
        mb.showerror(str(title), str(msg))
    except Exception:
        pass
    print(f"[{title}] {msg}")

if __name__ == "__main__":
    try:
        asyncio.run(AutoDialer().run())
    except KeyboardInterrupt:
        print("\n[!] Auto-Dialer stopped.")
        sys.exit(0)
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        try:
            with open(LOG_PATH, "a", encoding="utf-8") as f:
                f.write(f"\n[{ts()}] [CRITICAL] {tb}\n")
        except Exception:
            pass
        show_fatal_error("MCUBE Auto-Dialer Error", f"MCUBE Auto-Dialer encountered an error:\n\n{e}\n\nPlease check autodialer.log or ensure Google Chrome is available.")
        sys.exit(1)
