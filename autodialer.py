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
        candidates = [
            os.path.join(os.environ.get("ProgramFiles", "C:\\Program Files"), "Google\\Chrome\\Application\\chrome.exe"),
            os.path.join(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"), "Google\\Chrome\\Application\\chrome.exe"),
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Google\\Chrome\\Application\\chrome.exe"),
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
        ]
        for p in candidates:
            if os.path.isfile(p):
                return p
    elif sys.platform == "darwin":
        candidates = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            os.path.expanduser("~/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
        ]
        for p in candidates:
            if os.path.isfile(p):
                return p
    else:
        for cmd in ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser"]:
            found = shutil.which(cmd)
            if found:
                return found
    return None

def auto_launch_chrome():
    """Ensure Chrome is running with remote debugging port 9222."""
    if is_port_open("127.0.0.1", 9222):
        return True

    chrome_bin = get_chrome_executable()
    if not chrome_bin:
        log("Google Chrome binary not found in standard paths! Please launch Chrome manually with port 9222.", "WARN")
        return False

    if sys.platform == "win32":
        profile_dir = r"C:\chrome-autodial-profile"
    else:
        profile_dir = os.path.expanduser("~/chrome-autodial-profile")

    try:
        os.makedirs(profile_dir, exist_ok=True)
    except Exception:
        pass

    args = [
        chrome_bin,
        "--remote-debugging-port=9222",
        f"--user-data-dir={profile_dir}",
        "--no-first-run",
        "--no-default-browser-check",
        LSQ_MANAGE_URL,
        "https://dialer.mcube.com/index.html"
    ]

    log(f"Auto-launching Google Chrome on port 9222...", "INFO")
    try:
        subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        log(f"Failed to auto-launch Chrome: {e}", "ERR")
        return False

    # Wait up to 12 seconds for port 9222 to be available
    for _ in range(12):
        time.sleep(1)
        if is_port_open("127.0.0.1", 9222):
            log("Google Chrome is now running and listening on port 9222!", "OK")
            return True

    return False

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
            self.root.geometry("340x305+25+25")
            self.root.attributes("-topmost", True)
            self.root.resizable(False, False)
            self.root.configure(bg="#1E1E2E")

            self._status_lbl = tk.Label(
                self.root,
                text="STARTING...",
                font=("Segoe UI", 11, "bold"),
                fg="#F9E2AF",
                bg="#1E1E2E"
            )
            self._status_lbl.pack(pady=(10, 2), padx=10, anchor="w")

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
                command=lambda: self.loop.call_soon_threadsafe(self.customer_answered.set)
            ).pack(fill=tk.X, padx=10, pady=2)

            tk.Button(
                self.root,
                text="💾 Disposition Done (Resume)",
                font=("Segoe UI", 9),
                bg="#89B4FA",
                fg="#11111B",
                cursor="hand2",
                command=lambda: self.loop.call_soon_threadsafe(self.disposition_done.set)
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
            self.loop.call_soon_threadsafe(self.resume_event.set)

    def _stop(self):
        self.stopped = True
        self.loop.call_soon_threadsafe(self.skip_lead.set)
        try:
            self.root.quit()
        except Exception:
            pass

    def status(self, text):
        if self.root and self._status_lbl:
            try:
                self.root.after(0, lambda: self._status_lbl.config(text=text))
            except Exception:
                pass

    def lead(self, name):
        if self.root and self._lead_lbl:
            try:
                self.root.after(0, lambda: self._lead_lbl.config(text=f"Lead: {name[:30]}"))
            except Exception:
                pass

    def stats(self, dialed, connected, dnp):
        if self.root and self._stats_lbl:
            try:
                self.root.after(0, lambda: self._stats_lbl.config(
                    text=f"Dialed: {dialed} | Connected: {connected} | DNP: {dnp}"
                ))
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
        self.ctrl: Optional[MiniController] = None
        self.pw = None
        self.dialed = 0
        self.connected = 0
        self.dnp = 0
        self.processed = set()

    async def connect(self):
        """Connect to Chrome via CDP and find active pages with retry and auto-launch support."""
        if not is_port_open("127.0.0.1", 9222):
            log("Chrome is not listening on port 9222. Auto-launching Google Chrome...", "INFO")
            auto_launch_chrome()

        log("Connecting to Chrome on CDP port 9222...", "INFO")
        self.pw = await async_playwright().start()

        connected = False
        for attempt in range(1, 8):
            try:
                self.browser = await self.pw.chromium.connect_over_cdp(CDP_URL)
                connected = True
                break
            except Exception as e:
                if attempt == 1:
                    log(f"Waiting for Chrome on port 9222 (Attempt {attempt}/7)...", "WARN")
                await asyncio.sleep(2)

        if not connected:
            log(f"Cannot connect to Chrome on {CDP_URL}", "ERR")
            log("Please make sure Google Chrome is open with remote debugging enabled on port 9222!", "WARN")
            await self.pw.stop()
            return False

        log("Connected to Google Chrome successfully!", "OK")
        await self.find_pages()
        return True

    async def find_pages(self):
        """Dynamically detect or refresh LeadSquared and MCUBE pages."""
        self.lsq = None
        self.mcube = None

        # Prioritize exact Manage Opportunities tab
        for ctx in self.browser.contexts:
            for p in ctx.pages:
                if p.is_closed():
                    continue
                url = p.url.lower()

                # MCUBE Soft Phone popup
                if "dialer.mcube.com" in url and not self.mcube:
                    self.mcube = p
                    log(f"Found MCUBE Phone tab: {p.url[:60]}", "OK")

                # LeadSquared Manage Grid
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
                    if "opportunitymanagement" in url and "error" not in url:
                        self.lsq = p
                        log(f"Found LeadSquared page: {p.url[:60]}", "OK")
                        break

        # Fallback: create page if completely absent
        if not self.lsq:
            log(f"Opening LeadSquared grid: {LSQ_MANAGE_URL}", "INFO")
            ctx = self.browser.contexts[0] if self.browser.contexts else await self.browser.new_context()
            self.lsq = await ctx.new_page()
            await self.lsq.goto(LSQ_MANAGE_URL)

        # Attach auto-dialog accepter for native alerts/confirms
        if self.lsq:
            try:
                self.lsq.on("dialog", lambda dialog: asyncio.create_task(dialog.accept()))
            except Exception:
                pass

    async def ensure_on_grid(self):
        """Ensure self.lsq is on the Opportunity Management grid."""
        await self.find_pages()

        url = self.lsq.url.lower()

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
        Extract Sub Stage and Super Sub Stage from the Opportunity Details page.
        """
        try:
            return await self.lsq.evaluate("""() => {
                let subStage = '';
                let superSubStage = '';

                // 1. Look for table rows where first cell matches Sub Stage or Super Sub Stage
                const trs = Array.from(document.querySelectorAll('tr'));
                for (const tr of trs) {
                    const cells = Array.from(tr.querySelectorAll('td, th'));
                    if (cells.length >= 2) {
                        const lbl = cells[0].innerText.trim();
                        if (/^Sub\\s*Stage$/i.test(lbl)) {
                            subStage = cells[1].innerText.trim();
                        } else if (/^Super\\s*Sub\\s*Stage$/i.test(lbl)) {
                            superSubStage = cells[1].innerText.trim();
                        }
                    }
                }

                // 2. Look for dt/dd or label/value pairs
                if (!subStage || !superSubStage) {
                    const labels = Array.from(document.querySelectorAll('label, dt, .label, .field-label, span, div'));
                    for (const l of labels) {
                        const txt = l.innerText.trim();
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
                if (!subStage || !superSubStage) {
                    const lines = (document.body.innerText || '').split('\\n');
                    for (let i = 0; i < lines.length; i++) {
                        const line = lines[i].trim();
                        if (/^Sub\\s*Stage$/i.test(line) && i + 1 < lines.length && !subStage) {
                            subStage = lines[i + 1].trim();
                        }
                        if (/^Super\\s*Sub\\s*Stage$/i.test(line) && i + 1 < lines.length && !superSubStage) {
                            superSubStage = lines[i + 1].trim();
                        }
                    }
                }

                return { sub_stage: subStage, super_sub_stage: superSubStage };
            }""")
        except Exception:
            return {"sub_stage": "", "super_sub_stage": ""}

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

    async def monitor_call(self):
        """Monitor MCUBE soft phone popup state."""
        self.ctrl.status("📞 RINGING...")
        self.ctrl.customer_answered.clear()
        self.ctrl.skip_lead.clear()

        await self.find_pages()

        start = time.time()
        saw_in_progress = False

        while time.time() - start < RING_TIMEOUT:
            elapsed = int(time.time() - start)
            remaining = int(RING_TIMEOUT - elapsed)
            self.ctrl.status(f"📞 RINGING... ({remaining}s)")

            # Auto-click any remaining or late alert popups
            await self.dismiss_alerts()

            # Check manual override in mini-controller
            if self.ctrl.customer_answered.is_set():
                log("Manual Override: Customer Answered!", "OK")
                return "CONNECTED"

            if self.ctrl.skip_lead.is_set():
                log("Manual Skip clicked", "WARN")
                return "SKIPPED"

            # Check MCUBE popup status
            if self.mcube and not self.mcube.is_closed():
                try:
                    body = await self.mcube.inner_text("body")
                    lower = body.lower()

                    if "call in progress" in lower:
                        saw_in_progress = True

                    if "call ended" in lower or "disconnected" in lower:
                        log("MCUBE: Call ended (DNP)", "WARN")
                        return "DNP"

                    if "connected" in lower or "in call" in lower:
                        log("MCUBE: Customer Connected!", "OK")
                        return "CONNECTED"

                    if saw_in_progress and "call in progress" not in lower and elapsed > 5:
                        log("MCUBE: Call terminated (DNP)", "WARN")
                        return "DNP"
                except Exception:
                    pass

            await asyncio.sleep(0.5)

        log(f"Ring timeout ({RING_TIMEOUT}s) - Customer did not answer", "WARN")
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
        """Wait for agent to save disposition in LeadSquared."""
        self.ctrl.status("🗣️ IN CALL - SAVE DISPOSITION")
        self.ctrl.disposition_done.clear()
        log("Agent is on call. Save disposition in LeadSquared or click 'Disposition Done'...", "INFO")

        save_detected = asyncio.Event()

        def on_response(resp):
            try:
                if resp.status == 200 and resp.request.method == "POST":
                    url = resp.url.lower()
                    if any(k in url for k in ["save", "createactivity", "updateopportunity", "postactivity", "processform"]):
                        if not any(k in url for k in ["track", "ping", "notification", "keepalive", "log", "analytics"]):
                            log(f"Disposition save detected: {resp.url[:80]}", "OK")
                            save_detected.set()
            except Exception:
                pass

        self.lsq.on("response", on_response)

        try:
            while not save_detected.is_set() and not self.ctrl.disposition_done.is_set() and not self.ctrl.stopped:
                await asyncio.sleep(0.5)
        finally:
            try:
                self.lsq.remove_listener("response", on_response)
            except Exception:
                pass

        log("Disposition complete! Preparing next call...", "OK")
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

                # Check Sub Stage & Super Sub Stage before calling (exclude Invalid Lead / Not Interested)
                stages = await self.get_lead_sub_stages()
                sub = stages.get("sub_stage", "").strip()
                super_sub = stages.get("super_sub_stage", "").strip()
                if sub or super_sub:
                    log(f"Lead Sub Stage: '{sub}' | Super Sub Stage: '{super_sub}'", "INFO")

                should_skip = False
                skip_reason = ""
                for exc in EXCLUDE_SUB_STAGES:
                    if sub and exc.lower() in sub.lower():
                        should_skip = True
                        skip_reason = f"Sub Stage is '{sub}'"
                        break
                    if super_sub and exc.lower() in super_sub.lower():
                        should_skip = True
                        skip_reason = f"Super Sub Stage is '{super_sub}'"
                        break

                if should_skip:
                    log(f"🚫 SKIPPING LEAD ({lead['name']}): {skip_reason} (Excluded sub-stage)", "WARN")
                    self.ctrl.status(f"🚫 SKIPPED ({sub or super_sub})")
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
                    log(f"CALL CONNECTED: {lead['name']}", "OK")
                    self.connected += 1
                    self.ctrl.stats(self.dialed, self.connected, self.dnp)
                    play_connected_chime()
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


if __name__ == "__main__":
    try:
        asyncio.run(AutoDialer().run())
    except KeyboardInterrupt:
        print("\n[!] Auto-Dialer stopped.")
        sys.exit(0)
