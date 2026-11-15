#!/usr/bin/env python3
"""
MCUBE Dialer Diagnostic Sniffer
=================================
Attaches via Chrome DevTools Protocol (CDP) to an existing Chrome instance on
http://localhost:9222, identifies the MCUBE dialer popup (dialer.mcube.com),
and captures real-time:
  1. Console messages (JsSIP, SIP.js, WebRTC, ICE state transitions)
  2. WebSocket frames sent and received (raw SIP messages, JSON event envelopes)
  3. XHR / Fetch API requests & responses
  4. DOM Call Status transitions (e.g. "Call In Progress!", "Call ended")

Outputs formatted color-coded logs to terminal and saves full dump to 'mcube_sniff.log'.
"""

import asyncio
import datetime
import json
import os
import sys
from typing import Optional

import colorama
from colorama import Fore, Style
from playwright.async_api import BrowserContext, Page, Request, Response, WebSocket, async_playwright

colorama.init(autoreset=True)

CDP_URL = "http://localhost:9222"
LOG_FILE = "mcube_sniff.log"

# Key telephony indicators to highlight in logs
HIGHLIGHT_KEYWORDS = [
    "200 ok",
    "status",
    "answered",
    "connected",
    "confirmed",
    "accepted",
    "ringing",
    "progress",
    "bye",
    "cancel",
    "busy",
    "terminated",
    "failed",
    "rejected",
    "call in progress",
    "call ended",
    "jssip",
    "sip.js",
    "webrtc",
    "peerconnection",
    "iceconnectionstate",
]


def timestamp() -> str:
    return datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]


def log_to_file(category: str, data: str):
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp()}] [{category}] {data}\n")
    except Exception:
        pass


def highlight_text(text: str) -> str:
    """Highlights key telephony terms in bold cyan/green/yellow."""
    lower = text.lower()
    for kw in HIGHLIGHT_KEYWORDS:
        if kw in lower:
            return f"{Style.BRIGHT}{Fore.YELLOW}{text}{Style.RESET_ALL}"
    return text


def on_console_message(msg):
    text = msg.text
    msg_type = msg.type
    ts = timestamp()

    # Color code by severity
    if msg_type in ["error"]:
        prefix = f"{Fore.RED}[CONSOLE:{msg_type.upper()}]{Style.RESET_ALL}"
    elif msg_type in ["warning", "warn"]:
        prefix = f"{Fore.MAGENTA}[CONSOLE:{msg_type.upper()}]{Style.RESET_ALL}"
    else:
        prefix = f"{Fore.BLUE}[CONSOLE:{msg_type.upper()}]{Style.RESET_ALL}"

    formatted = highlight_text(text)
    print(f"{Fore.LIGHTBLACK_EX}{ts}{Style.RESET_ALL} {prefix} {formatted}")
    log_to_file(f"CONSOLE:{msg_type}", text)


def setup_websocket_listeners(ws: WebSocket):
    ws_url = ws.url
    ts = timestamp()
    print(f"{Fore.LIGHTBLACK_EX}{ts}{Style.RESET_ALL} {Fore.CYAN}[WS:OPEN]{Style.RESET_ALL} Connected to: {ws_url}")
    log_to_file("WS:OPEN", ws_url)

    def on_framesent(payload):
        t = timestamp()
        text = payload if isinstance(payload, str) else f"<binary {len(payload)} bytes>"
        # Format if JSON
        formatted_preview = format_payload_preview(text)
        print(f"{Fore.LIGHTBLACK_EX}{t}{Style.RESET_ALL} {Fore.GREEN}[WS >> OUT]{Style.RESET_ALL} {formatted_preview}")
        log_to_file("WS:SENT", text)

    def on_framereceived(payload):
        t = timestamp()
        text = payload if isinstance(payload, str) else f"<binary {len(payload)} bytes>"
        formatted_preview = format_payload_preview(text)
        highlighted = highlight_text(formatted_preview)
        print(f"{Fore.LIGHTBLACK_EX}{t}{Style.RESET_ALL} {Fore.GREEN}{Style.BRIGHT}[WS << IN]{Style.RESET_ALL} {highlighted}")
        log_to_file("WS:RECV", text)

    def on_close():
        t = timestamp()
        print(f"{Fore.LIGHTBLACK_EX}{t}{Style.RESET_ALL} {Fore.CYAN}[WS:CLOSED]{Style.RESET_ALL} {ws_url}")
        log_to_file("WS:CLOSED", ws_url)

    ws.on("framesent", on_framesent)
    ws.on("framereceived", on_framereceived)
    ws.on("close", on_close)


def format_payload_preview(payload_str: str) -> str:
    """Pretty formats single-line JSON or compresses multi-line SIP messages for neat terminal display."""
    payload_clean = payload_str.strip()
    if payload_clean.startswith("{") or payload_clean.startswith("["):
        try:
            parsed = json.loads(payload_clean)
            return json.dumps(parsed)
        except Exception:
            pass
    # If SIP message (multiline starting with SIP/ or method)
    lines = [line.strip() for line in payload_clean.splitlines() if line.strip()]
    if len(lines) > 1:
        return " | ".join(lines[:4]) + (f" ... ({len(lines)} lines)" if len(lines) > 4 else "")
    return payload_clean[:300]


def setup_network_listeners(page: Page):
    async def on_request(request: Request):
        # Filter static assets
        resource_type = request.resource_type
        if resource_type in ["image", "media", "font", "stylesheet"]:
            return
        url = request.url
        t = timestamp()
        method = request.method
        post_data = request.post_data
        post_preview = f" Body: {post_data[:120]}" if post_data else ""
        print(f"{Fore.LIGHTBLACK_EX}{t}{Style.RESET_ALL} {Fore.YELLOW}[HTTP:REQ]{Style.RESET_ALL} {method} {url}{post_preview}")
        log_to_file("HTTP:REQ", f"{method} {url} {post_data or ''}")

    async def on_response(response: Response):
        resource_type = response.request.resource_type
        if resource_type in ["image", "media", "font", "stylesheet"]:
            return
        t = timestamp()
        status = response.status
        url = response.url
        status_color = Fore.GREEN if status < 400 else Fore.RED
        
        # Check if JSON response
        body_preview = ""
        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type or "text/" in content_type:
            try:
                body = await response.text()
                if body:
                    body_preview = f" -> {body[:150]}"
            except Exception:
                pass

        print(
            f"{Fore.LIGHTBLACK_EX}{t}{Style.RESET_ALL} {Fore.YELLOW}[HTTP:RES]{Style.RESET_ALL} "
            f"{status_color}{status}{Style.RESET_ALL} {url}{body_preview}"
        )
        log_to_file("HTTP:RES", f"{status} {url} {body_preview}")

    page.on("request", on_request)
    page.on("response", on_response)


async def poll_dom_status(page: Page):
    """Continuously monitor MCUBE dialer DOM body text for status shifts."""
    last_snippet = ""
    while not page.is_closed():
        try:
            body_text = await page.inner_text("body")
            # Look for common status phrases
            status_lines = []
            for line in body_text.splitlines():
                l = line.strip()
                if any(k in l.lower() for k in ["call", "progress", "ring", "connect", "status", "ready", "agent"]):
                    if len(l) < 80:
                        status_lines.append(l)

            current_snippet = " // ".join(status_lines[:3])
            if current_snippet and current_snippet != last_snippet:
                last_snippet = current_snippet
                t = timestamp()
                print(
                    f"{Fore.LIGHTBLACK_EX}{t}{Style.RESET_ALL} "
                    f"{Fore.MAGENTA}{Style.BRIGHT}[DOM:STATUS]{Style.RESET_ALL} {current_snippet}"
                )
                log_to_file("DOM:STATUS", current_snippet)
        except Exception:
            pass
        await asyncio.sleep(0.7)


async def find_mcube_page(contexts: list[BrowserContext]) -> Optional[Page]:
    """Scan all open tabs/windows across all contexts for MCUBE."""
    for ctx in contexts:
        for p in ctx.pages:
            try:
                url = p.url.lower()
                if "dialer.mcube.com" in url or "mcube" in url:
                    return p
            except Exception:
                continue
    return None


async def attach_and_sniff(mcube_page: Page):
    print(f"\n{Fore.GREEN}{Style.BRIGHT}[+] Attached to MCUBE dialer: {mcube_page.url}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}[*] Hooking Console messages, WebSockets, XHR responses, and DOM changes...{Style.RESET_ALL}")
    print(f"{Fore.CYAN}[*] Logging detailed output to: {os.path.abspath(LOG_FILE)}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}[!] Trigger a test call from LeadSquared to observe Leg-A vs Leg-B events.{Style.RESET_ALL}\n")
    print("-" * 80)

    # 1. Console listener
    mcube_page.on("console", on_console_message)

    # 2. WebSocket listener (Playwright high-level)
    mcube_page.on("websocket", setup_websocket_listeners)

    # 2b. Low-level CDP session listener (Captures frames from pre-existing WebSockets)
    cdp_session = None
    try:
        cdp_session = await mcube_page.context.new_cdp_session(mcube_page)
        await cdp_session.send("Network.enable")

        def on_cdp_ws_frame_recv(params):
            resp = params.get("response", {})
            payload = resp.get("payloadData", "")
            if payload:
                t = timestamp()
                preview = highlight_text(format_payload_preview(payload))
                print(f"{Fore.LIGHTBLACK_EX}{t}{Style.RESET_ALL} {Fore.GREEN}{Style.BRIGHT}[CDP-WS << IN]{Style.RESET_ALL} {preview}")
                log_to_file("CDP-WS:RECV", payload)

        def on_cdp_ws_frame_sent(params):
            resp = params.get("response", {})
            payload = resp.get("payloadData", "")
            if payload:
                t = timestamp()
                preview = format_payload_preview(payload)
                print(f"{Fore.LIGHTBLACK_EX}{t}{Style.RESET_ALL} {Fore.GREEN}[CDP-WS >> OUT]{Style.RESET_ALL} {preview}")
                log_to_file("CDP-WS:SENT", payload)

        cdp_session.on("Network.webSocketFrameReceived", on_cdp_ws_frame_recv)
        cdp_session.on("Network.webSocketFrameSent", on_cdp_ws_frame_sent)
        print(f"{Fore.GREEN}[*] Attached low-level CDP Network session (capturing pre-existing WebSockets){Style.RESET_ALL}")
    except Exception as e:
        log_to_file("CDP:WARN", f"Could not create CDP session: {e}")

    # 3. HTTP listener
    setup_network_listeners(mcube_page)

    # 4. Background DOM poller
    dom_task = asyncio.create_task(poll_dom_status(mcube_page))

    try:
        # Keep alive until user interrupts or page closes
        while not mcube_page.is_closed():
            await asyncio.sleep(1)
    finally:
        dom_task.cancel()


async def main():
    print(f"{Fore.CYAN}{Style.BRIGHT}================================================================={Style.RESET_ALL}")
    print(f"{Fore.CYAN}{Style.BRIGHT}        MCUBE Browser Phone WebRTC & SIP Diagnostic Sniffer       {Style.RESET_ALL}")
    print(f"{Fore.CYAN}{Style.BRIGHT}================================================================={Style.RESET_ALL}")
    print(f"Connecting to Chrome DevTools Protocol at {CDP_URL} ...")

    async with async_playwright() as pw:
        try:
            browser = await pw.chromium.connect_over_cdp(CDP_URL)
        except Exception as e:
            print(f"\n{Fore.RED}[ERROR] Could not connect to Chrome on {CDP_URL}:{Style.RESET_ALL} {e}")
            print(f"{Fore.YELLOW}Tip: Ensure Chrome was launched via 'launch_chrome.bat' with --remote-debugging-port=9222{Style.RESET_ALL}")
            return

        print(f"{Fore.GREEN}[OK] Connected to Chrome instance! Scanning active contexts...{Style.RESET_ALL}")

        contexts = browser.contexts
        if not contexts:
            print(f"{Fore.RED}[ERROR] No browser contexts found.{Style.RESET_ALL}")
            return

        mcube_page = await find_mcube_page(contexts)

        if not mcube_page:
            print(f"{Fore.YELLOW}[!] MCUBE dialer page (dialer.mcube.com) was not found in open tabs.{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}[*] Available open pages:{Style.RESET_ALL}")
            for i, ctx in enumerate(contexts):
                for j, p in enumerate(ctx.pages):
                    print(f"    - [{i}:{j}] {p.url} ('{await p.title()}')")

            print(f"\n{Fore.CYAN}[*] Waiting for MCUBE dialer popup to open (listening for new tabs/popups)...{Style.RESET_ALL}")
            print(f"{Fore.WHITE}    (Open https://dialer.mcube.com/index.html or click to call in CRM){Style.RESET_ALL}")

            found_event = asyncio.Event()
            detected_page = {"page": None}

            def check_new_page(p: Page):
                async def check_url():
                    try:
                        # Wait briefly for URL navigation if blank
                        await p.wait_for_load_state("domcontentloaded", timeout=4000)
                    except Exception:
                        pass
                    if "dialer.mcube.com" in p.url.lower() or "mcube" in p.url.lower():
                        detected_page["page"] = p
                        found_event.set()
                asyncio.create_task(check_url())

            for ctx in contexts:
                ctx.on("page", check_new_page)

            # Polling loop in case popup was already opening
            for _ in range(60):
                if found_event.is_set():
                    break
                mcube_page = await find_mcube_page(contexts)
                if mcube_page:
                    break
                await asyncio.sleep(1)

            if not mcube_page and detected_page["page"]:
                mcube_page = detected_page["page"]

            if not mcube_page:
                print(f"{Fore.RED}[TIMEOUT] MCUBE dialer popup was not detected after 60 seconds.{Style.RESET_ALL}")
                return

        await attach_and_sniff(mcube_page)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[*] Sniffer stopped by user. Log saved to {LOG_FILE}{Style.RESET_ALL}")
        sys.exit(0)
