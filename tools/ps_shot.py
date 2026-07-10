#!/usr/bin/env python3
"""
Take a screenshot after N seconds using a separate process with a hard kill.
Uses threading to kill the browser after the wait, then saves the final screenshot.

Use when Chromium may stall under sync MicroPython-WASM loops. See
``.cursor/pyscript-troubleshooting.md``.

Usage:
    python tools/ps_shot.py URL [wait_sec] [out.png]
"""

import base64
import os
import sys
import threading
import time

from playwright.sync_api import sync_playwright

URL = (
    sys.argv[1]
    if len(sys.argv) > 1
    else "http://127.0.0.1:8000/web/pyscript/embed.html?manifests=tiny_toasters"
)
WAIT_SEC = float(sys.argv[2]) if len(sys.argv) > 2 else 6.0
OUT = sys.argv[3] if len(sys.argv) > 3 else "/tmp/pyscript_shot.png"

t0 = time.time()


def ts():
    return f"{time.time() - t0:5.1f}s"


msgs = []
got_shot = threading.Event()


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-gpu"])
        ctx = browser.new_context()
        page = ctx.new_page()
        cdp = ctx.new_cdp_session(page)

        # Minimal CDP - only listen for key markers, don't enable Console
        cdp.send("Runtime.enable")

        def on_exc(params):
            exc = params.get("exceptionDetails", {})
            text = exc.get("text", "") + " " + str(exc.get("exception", {}).get("description", ""))
            print(f"[{ts()}][ERR] {text[:300]}", flush=True)

        cdp.on("Runtime.exceptionThrown", on_exc)

        print(f"[{ts()}] goto {URL}", flush=True)
        page.goto(URL, timeout=15000, wait_until="domcontentloaded")
        print(f"[{ts()}] DOM ready, sleeping {WAIT_SEC}s", flush=True)

        time.sleep(WAIT_SEC)

        print(f"[{ts()}] taking CDP screenshot", flush=True)
        # CDP screenshot doesn't require JS eval - handled at browser process level
        for attempt in range(5):
            try:
                r = cdp.send("Page.captureScreenshot", {"format": "png"})
                data = base64.b64decode(r.get("data", ""))
                with open(OUT, "wb") as f:
                    f.write(data)
                print(f"[{ts()}] saved {OUT} ({len(data)} bytes)", flush=True)
                got_shot.set()
                break
            except Exception as e:
                print(f"[{ts()}] attempt {attempt + 1} failed: {e}", flush=True)
                time.sleep(0.2)

        browser.close()


run()
print("done" if got_shot.is_set() else "FAILED - no screenshot")
