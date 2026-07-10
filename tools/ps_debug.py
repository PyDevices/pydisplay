#!/usr/bin/env python3
"""
Thorough PyScript debug runner — captures all JS console output via CDP,
monitors #log div for Python print() output, tracks network requests,
and checks for WASM loading errors.

Prefer this over Cursor Browser screenshots when sync Python may be blocking
the main thread (``page.evaluate`` / screenshots often hang). See
``.cursor/pyscript-troubleshooting.md``.

Usage:
    python tools/ps_debug.py URL [timeout_sec]
"""

import json
import sys
import time

from playwright.sync_api import TimeoutError as PwTimeout
from playwright.sync_api import sync_playwright

URL = (
    sys.argv[1]
    if len(sys.argv) > 1
    else ("http://127.0.0.1:8000/web/pyscript/embed.html?modules=bouncing_balls&debug=1")
)
TIMEOUT_SEC = int(sys.argv[2]) if len(sys.argv) > 2 else 25

t0 = time.time()
all_events = []


def ts():
    return f"{time.time() - t0:6.1f}s"


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-gpu",
                "--enable-features=SharedArrayBuffer",
                # Explicitly enable COOP/COEP so SharedArrayBuffer works
                "--disable-web-security",
                "--allow-running-insecure-content",
            ],
        )
        ctx = browser.new_context(
            # Force cross-origin isolated context so SharedArrayBuffer/WASM threads work
            extra_http_headers={
                "Cross-Origin-Opener-Policy": "same-origin",
                "Cross-Origin-Embedder-Policy": "require-corp",
            }
        )
        page = ctx.new_page()

        # Enable CDP console + runtime for all message types
        cdp = ctx.new_cdp_session(page)
        cdp.send("Console.enable")
        cdp.send("Runtime.enable")
        cdp.send("Log.enable")

        def on_console_api(params):
            args = params.get("args", [])
            texts = []
            for a in args:
                if a.get("type") == "string":
                    texts.append(a.get("value", ""))
                else:
                    texts.append(str(a.get("value", a.get("description", "?"))))
            text = " ".join(texts)
            t = params.get("type", "log")
            print(f"[{ts()}][cdp:{t}] {text[:400]}", flush=True)
            all_events.append({"src": "cdp", "type": t, "text": text})

        def on_log_entry(params):
            entry = params.get("entry", {})
            text = entry.get("text", "")
            lvl = entry.get("level", "info")
            print(f"[{ts()}][log:{lvl}] {text[:400]}", flush=True)
            all_events.append({"src": "log", "level": lvl, "text": text})

        def on_exception(params):
            exc = params.get("exceptionDetails", {})
            text = exc.get("text", "") + " " + str(exc.get("exception", {}).get("description", ""))
            print(f"[{ts()}][EXCEPTION] {text[:600]}", flush=True)
            all_events.append({"src": "exception", "text": text})

        cdp.on("Runtime.consoleAPICalled", on_console_api)
        cdp.on("Log.entryAdded", on_log_entry)
        cdp.on("Runtime.exceptionThrown", on_exception)

        # Network tracking
        network_fails = []

        def on_request_failed(req):
            msg = f"FAILED {req.url[:120]} — {req.failure}"
            print(f"[{ts()}][net:FAIL] {msg}", flush=True)
            network_fails.append(msg)

        page.on("requestfailed", on_request_failed)

        print(f"[{ts()}] Navigating to: {URL}", flush=True)
        try:
            page.goto(URL, timeout=15000, wait_until="domcontentloaded")
            print(f"[{ts()}] DOM ready", flush=True)
        except PwTimeout:
            print(f"[{ts()}][WARN] DOMContentLoaded timed out; continuing", flush=True)

        # Poll for Python #log output every 2s
        deadline = time.time() + TIMEOUT_SEC
        last_log = ""
        while time.time() < deadline:
            time.sleep(2.0)
            try:
                log_text = page.evaluate(
                    "() => { var e = document.getElementById('log'); return e ? e.textContent : null; }"
                )
                if log_text and log_text != last_log:
                    print(
                        f"\n[{ts()}]=== #log div (new content) ===\n{log_text.strip()}\n",
                        flush=True,
                    )
                    last_log = log_text
            except Exception as e:
                print(f"[{ts()}][eval error] {e}", flush=True)

        # Final DOM evaluation
        print(f"\n[{ts()}]=== Final page state ===", flush=True)
        try:
            result = page.evaluate("""() => ({
                logText: (document.getElementById('log') || {}).textContent || '',
                title: document.title,
                readyState: document.readyState,
                pyErrors: window.__pyErrors || [],
            })""")
            print(json.dumps(result, indent=2), flush=True)
        except Exception as e:
            print(f"[eval error] {e}", flush=True)

        try:
            page.screenshot(path="/tmp/pyscript_debug.png", timeout=5000)
            print(f"[{ts()}][screenshot] saved to /tmp/pyscript_debug.png", flush=True)
        except Exception as e:
            print(f"[{ts()}][screenshot error] {e}", flush=True)

        if network_fails:
            print("\n=== Network failures ===")
            for f in network_fails:
                print(f"  {f}")

        browser.close()


if __name__ == "__main__":
    run()
