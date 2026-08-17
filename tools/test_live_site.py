#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Brad Barnett
# SPDX-License-Identifier: MIT
"""Test PyScript HTML shells against the live deployed GitHub Pages site."""

import asyncio
import sys

from playwright.async_api import async_playwright

LIVE_BASE_URL = "https://pydevices.github.io/pydevices-examples/pyscript"

PAGES = [
    ("DOM Event Test", "dom.html"),
    ("Async Animation Test", "async.html"),
    ("MicroPython Paint", "micropython.html?modules=paint"),
    ("Pyodide Paint", "pyodide.html?modules=paint"),
    ("Compact MP Runner", "mp.html?modules=paint"),
    ("Compact Pyodide Runner", "py.html?modules=paint"),
    ("Autotest Harness", "harness.html?modules=paint"),
    ("Interactive Editor", "editor.html"),
    ("Interactive REPL", "repl.html"),
    ("Peter Hinch GUI Demos", "peterhinch.html?touch"),
]


async def run_live_tests():
    print("=" * 70)
    print(f"TESTING LIVE SITE: {LIVE_BASE_URL}")
    print("=" * 70)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        console_logs = []
        page_errors = []
        network_failures = []

        page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))
        page.on("pageerror", lambda err: page_errors.append(str(err)))
        page.on(
            "requestfailed",
            lambda req: network_failures.append(f"{req.url} -> {req.failure}"),
        )

        results = []

        for title, rel_path in PAGES:
            console_logs.clear()
            page_errors.clear()
            network_failures.clear()

            url = f"{LIVE_BASE_URL}/{rel_path}"
            print(f"\nEvaluating: {title} ({url})")

            try:
                response = await page.goto(url, wait_until="domcontentloaded", timeout=20000)
                status_code = response.status if response else "NO_RESPONSE"
                await page.wait_for_timeout(5000)

                status_el = await page.query_selector("#status")
                status_text = (await status_el.text_content()).strip() if status_el else None

                log_el = await page.query_selector("#log")
                log_text = (await log_el.text_content()).strip() if log_el else None

                res_info = {
                    "title": title,
                    "url": url,
                    "status_code": status_code,
                    "status_text": status_text,
                    "log_text": log_text,
                    "errors": list(page_errors),
                    "network_failures": list(network_failures),
                    "console": list(console_logs),
                }
                results.append(res_info)

                print(f"  HTTP Status: {status_code}")
                if status_text:
                    print(f"  Page Status: {status_text}")
                if page_errors:
                    print(f"  Page Errors ({len(page_errors)}): {page_errors}")
                if network_failures:
                    print(f"  Network Failures ({len(network_failures)}): {network_failures}")
                if not page_errors and not network_failures:
                    print("  Result: Loaded without errors.")

            except Exception as exc:
                print(f"  [ERROR] Navigation failed: {exc}")
                results.append(
                    {
                        "title": title,
                        "url": url,
                        "status_code": "EXCEPTION",
                        "error": str(exc),
                    }
                )

        await browser.close()

    print("\n" + "=" * 70)
    print("LIVE SITE REPORT SUMMARY")
    print("=" * 70)
    for r in results:
        code = r.get("status_code")
        errs = len(r.get("errors", []))
        net_fails = len(r.get("network_failures", []))
        print(f"{r['title']:25s} | HTTP {code} | Errors: {errs} | Net Fails: {net_fails}")
        if r.get("status_text"):
            print(f"   Status element: {r['status_text']}")
        if r.get("errors"):
            for e in r["errors"]:
                print(f"   Page Error: {e}")
        if r.get("network_failures"):
            for nf in r["network_failures"]:
                print(f"   Network Failure: {nf}")


if __name__ == "__main__":
    asyncio.run(run_live_tests())
