#!/usr/bin/env python3
"""
Screenshot-only PyScript runner. Navigates, waits N seconds, takes a screenshot.
Uses CDP console-only monitoring (no page.evaluate which hangs during ASYNCIFY /
sync WASM sleep). See ``.cursor/pyscript-troubleshooting.md``.

Usage:
    python tools/ps_screenshot.py URL [wait_sec] [out.png]
"""

import sys
import threading
import time

from playwright.sync_api import TimeoutError as PwTimeout
from playwright.sync_api import sync_playwright

URL = (
    sys.argv[1]
    if len(sys.argv) > 1
    else "http://127.0.0.1:8000/web/pyscript/embed.html?manifests=tiny_toasters&debug=1"
)
WAIT_SEC = int(sys.argv[2]) if len(sys.argv) > 2 else 8
OUT_PNG = sys.argv[3] if len(sys.argv) > 3 else "/tmp/pyscript_screenshot.png"

t0 = time.time()


def ts():
    return f"{time.time() - t0:5.1f}s"


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-gpu"])
        ctx = browser.new_context()
        page = ctx.new_page()
        cdp = ctx.new_cdp_session(page)
        cdp.send("Console.enable")
        cdp.send("Runtime.enable")
        cdp.send("Log.enable")

        msgs = []

        def on_console(params):
            args = params.get("args", [])
            text = " ".join(a.get("value", "") for a in args if a.get("type") == "string")
            if text:
                msgs.append(f"[{ts()}] {text[:200]}")
                if "pydisplay" in text or "Runtime" in text or "Error" in text:
                    print(f"[{ts()}] {text[:200]}", flush=True)

        def on_exc(params):
            exc = params.get("exceptionDetails", {})
            text = exc.get("text", "") + " " + str(exc.get("exception", {}).get("description", ""))
            print(f"[{ts()}][EXCEPTION] {text[:400]}", flush=True)

        cdp.on("Runtime.consoleAPICalled", on_console)
        cdp.on("Runtime.exceptionThrown", on_exc)

        print(f"[{ts()}] Navigating to {URL}", flush=True)
        try:
            page.goto(URL, timeout=12000, wait_until="domcontentloaded")
        except PwTimeout:
            print(f"[{ts()}] DOMContentLoaded timeout (continuing)", flush=True)

        print(f"[{ts()}] Waiting {WAIT_SEC}s...", flush=True)
        time.sleep(WAIT_SEC)

        # Screenshot via CDP (doesn't require JS eval)
        print(f"[{ts()}] Taking CDP screenshot...", flush=True)
        try:
            result = cdp.send("Page.captureScreenshot", {"format": "png", "quality": 80})
            import base64

            data = base64.b64decode(result.get("data", ""))
            with open(OUT_PNG, "wb") as f:
                f.write(data)
            print(f"[{ts()}] Screenshot saved: {OUT_PNG} ({len(data)} bytes)", flush=True)
        except Exception as e:
            print(f"[{ts()}] CDP screenshot error: {e}", flush=True)

        print(f"\n--- Console messages ({len(msgs)}) ---")
        for m in msgs[:50]:
            print(m)
        if len(msgs) > 50:
            print(f"... and {len(msgs) - 50} more")

        browser.close()


run()
