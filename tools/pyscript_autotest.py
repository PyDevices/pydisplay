#!/usr/bin/env python3
"""PyScript example autotest: console watch → Ctrl+Q quit chord → EXAMPLE_RESULT.

Flow:
  1. Load ``embed.html?...&autotest=1``
  2. Wait until the demo has imported (``AUTOTEST_READY`` / ``MARK:after_import_entry``)
  3. Soak ``duration_s`` while monitoring console + pageerrors (fail on real errors)
  4. Focus ``#display_canvas`` and send the default quit chord **Ctrl+Q**
  5. Wait for ``EXAMPLE_RESULT=`` (embed emits it from ``runtime.before_quit``)

Python ``print`` on embed goes to the page ``#log`` panel (not always the
browser console). When ``stream_log=True`` (CLI / ``pyscript.sh --autotest``),
new ``#log`` lines are mirrored to stdout in real time.

Usage:
  .venv/bin/python tools/pyscript_autotest.py \\
    'http://127.0.0.1:8000/web/pyscript/embed.html?modules=pydisplay_demo&autotest=1&duration=5'
"""

from __future__ import annotations

import json
import re
import sys
import time
from typing import Any
from urllib.parse import parse_qs, urlparse

# Console noise that is not a demo failure.
_IGNORE_ERROR_SUBSTR = (
    "Failed to execute 'fetch' on 'Window'",  # optional debug POST
    "net::ERR_",  # transient CDN/cache; pageerror path still catches hard fails
    "ResizeObserver loop",
)

_READY_MARKERS = (
    "AUTOTEST_READY=",
    "MARK:after_import_entry",
)

_TRACE_RE = re.compile(
    r"(?i)(traceback \(most recent call last\)|^  file \"|importerror:|modulenotfounderror:|"
    r"syntaxerror:|memoryerror:|typeerror:|attributeerror:|runtimeerror:|oserror:)"
)


def _is_ignored(text: str) -> bool:
    return any(s in text for s in _IGNORE_ERROR_SUBSTR)


def _looks_like_py_error(text: str) -> bool:
    if _is_ignored(text):
        return False
    if text.startswith("EXAMPLE_RESULT="):
        return False
    if text.startswith("MARK:"):
        return False
    return bool(_TRACE_RE.search(text))


def example_name_from_url(url: str) -> str:
    q = parse_qs(urlparse(url).query)
    for key in ("modules", "manifests"):
        vals = q.get(key) or []
        if vals:
            return vals[0].split(",")[0]
    return "?"


class _LogStreamer:
    """Poll embed ``#log`` and print new lines to stdout."""

    def __init__(self, page, *, enabled: bool = True, prefix: str = "[#log] "):
        self._page = page
        self._enabled = enabled
        self._prefix = prefix
        self._seen = ""
        self.lines: list[str] = []

    def poll(self) -> list[str]:
        if not self._enabled:
            return []
        try:
            text = (
                self._page.evaluate(
                    "() => { const el = document.getElementById('log');"
                    " return el ? el.textContent : ''; }"
                )
                or ""
            )
        except Exception:
            return []
        if text == self._seen:
            return []
        chunk = text[len(self._seen) :] if text.startswith(self._seen) else text
        self._seen = text
        new_lines: list[str] = []
        for line in chunk.splitlines():
            if not line.strip():
                continue
            new_lines.append(line)
            self.lines.append(line)
            if self._prefix:
                print(f"{self._prefix}{line}", flush=True)
        return new_lines


def run_autotest(
    url: str,
    *,
    duration_s: float = 5.0,
    timeout_s: float = 45.0,
    soak_s: float | None = None,
    stream_log: bool = False,
) -> dict[str, Any]:
    """Return an EXAMPLE_RESULT-compatible dict (always has status).

    ``stream_log``: when True (``pyscript.sh --autotest`` / CLI), mirror ``#log``
    lines to stdout as they appear.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        return {
            "example": example_name_from_url(url),
            "status": "error",
            "error": f"playwright not installed: {exc}",
            "runtime": "pyscript",
        }

    soak = float(duration_s if soak_s is None else soak_s)
    example = example_name_from_url(url)
    console_msgs: list[dict[str, str]] = []
    page_errors: list[str] = []
    results: list[dict[str, Any]] = []
    ready = False
    t0 = time.monotonic()

    def elapsed() -> float:
        return time.monotonic() - t0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        # Always collect #log for diagnostics; only mirror to stdout when requested.
        log = _LogStreamer(page, enabled=True, prefix="[#log] " if stream_log else "")

        def on_console(msg) -> None:
            nonlocal ready
            text = msg.text or ""
            typ = msg.type or "log"
            console_msgs.append({"type": typ, "text": text, "t": f"{elapsed():.2f}"})
            if text.startswith("EXAMPLE_RESULT="):
                try:
                    results.append(json.loads(text.split("=", 1)[1]))
                except Exception:
                    pass
            if any(m in text for m in _READY_MARKERS):
                ready = True

        page.on("console", on_console)
        page.on("pageerror", lambda exc: page_errors.append(str(exc)))

        try:
            page.goto(url, wait_until="load", timeout=int(timeout_s * 1000))
        except Exception as exc:
            browser.close()
            return {
                "example": example,
                "status": "error",
                "error": f"page.goto failed: {exc}",
                "runtime": "pyscript",
            }

        # --- wait for import ready (or early EXAMPLE_RESULT error) ---
        ready_deadline = time.monotonic() + max(25.0, timeout_s * 0.6)
        while time.monotonic() < ready_deadline:
            log.poll()
            if results:
                break
            if ready:
                break
            # Import failure often prints EXAMPLE_RESULT immediately.
            if any(m["type"] == "error" and _looks_like_py_error(m["text"]) for m in console_msgs):
                break
            if any(_looks_like_py_error(line) for line in log.lines):
                break
            page.wait_for_timeout(100)

        log.poll()

        if results and results[0].get("status") != "ok":
            browser.close()
            return results[0]

        early_errs = [
            m["text"]
            for m in console_msgs
            if (m["type"] == "error" and not _is_ignored(m["text"]))
            or _looks_like_py_error(m["text"])
        ]
        early_errs.extend(page_errors)
        early_errs.extend(line for line in log.lines if _looks_like_py_error(line))
        if early_errs and not ready:
            browser.close()
            return {
                "example": example,
                "status": "error",
                "error": early_errs[0][:300],
                "runtime": "pyscript",
                "console_errors": early_errs[:5],
            }

        # --- soak: demo runs; fail on console/page errors ---
        soak_end = time.monotonic() + soak
        soak_errors: list[str] = []
        while time.monotonic() < soak_end:
            for line in log.poll():
                if _looks_like_py_error(line) and line not in soak_errors:
                    soak_errors.append(line)
            for m in console_msgs:
                text = m["text"]
                if (
                    m["type"] == "error" and not _is_ignored(text) and text not in soak_errors
                ) or (_looks_like_py_error(text) and text not in soak_errors):
                    soak_errors.append(text)
            for e in page_errors:
                if e not in soak_errors:
                    soak_errors.append(e)
            if soak_errors:
                break
            if results:
                # Unexpected early finish during soak
                break
            page.wait_for_timeout(100)

        if soak_errors:
            # Coalesce trailing traceback / exception lines before declaring failure.
            coalesce_end = time.monotonic() + 0.8
            while time.monotonic() < coalesce_end:
                for line in log.poll():
                    if line not in soak_errors:
                        soak_errors.append(line)
                for m in console_msgs:
                    text = m["text"]
                    if (
                        text
                        and text not in soak_errors
                        and (m["type"] == "error" or _looks_like_py_error(text))
                    ):
                        soak_errors.append(text)
                page.wait_for_timeout(50)
            browser.close()
            return {
                "example": example,
                "status": "error",
                "error": soak_errors[0][:300],
                "runtime": "pyscript",
                "phase": "soak",
                "console_errors": soak_errors[:20],
            }

        # --- quit chord: Ctrl+Q (displaysys.default_quit_chord) ---
        try:
            canvas = page.locator("#display_canvas")
            canvas.click(timeout=5000)
            # Prefer CDP trusted key events: synthetic KeyboardEvent often does
            # not reach Pyodide create_proxy listeners; Chromium also swallows
            # real Ctrl+Q as a browser quit chord.
            try:
                cdp = page.context.new_cdp_session(page)
                # modifiers: 2 = Ctrl
                for typ in ("keyDown", "keyUp"):
                    cdp.send(
                        "Input.dispatchKeyEvent",
                        {
                            "type": typ,
                            "modifiers": 2,
                            "key": "q",
                            "code": "KeyQ",
                            "windowsVirtualKeyCode": 81,
                            "nativeVirtualKeyCode": 81,
                            "text": "",
                            "unmodifiedText": "",
                        },
                    )
            except Exception as cdp_exc:
                page.evaluate(
                    """() => {
                      const c = document.getElementById('display_canvas');
                      if (!c) return {ok: false, reason: 'no #display_canvas'};
                      c.focus();
                      const opts = {
                        key: 'q', code: 'KeyQ', keyCode: 113, which: 113,
                        ctrlKey: true, bubbles: true, cancelable: true
                      };
                      c.dispatchEvent(new KeyboardEvent('keydown', opts));
                      c.dispatchEvent(new KeyboardEvent('keyup', opts));
                      return {
                        ok: true,
                        via: 'dispatchEvent',
                        activeId: document.activeElement && document.activeElement.id,
                        cdpError: %s
                      };
                    }"""
                    % json.dumps(str(cdp_exc))
                )
            console_msgs.append(
                {
                    "type": "info",
                    "text": "AUTOTEST_QUIT_CHORD=Control+q",
                    "t": f"{elapsed():.2f}",
                }
            )
            if stream_log:
                print("[#log] AUTOTEST_QUIT_CHORD=Control+q", flush=True)
        except Exception as exc:
            browser.close()
            return {
                "example": example,
                "status": "error",
                "error": f"quit chord failed: {exc}",
                "runtime": "pyscript",
                "phase": "quit_chord",
            }

        # --- watch for EXAMPLE_RESULT after quit ---
        quit_deadline = time.monotonic() + max(10.0, soak)
        while time.monotonic() < quit_deadline:
            log.poll()
            if results:
                break
            for m in console_msgs:
                text = m["text"]
                if m["type"] == "error" and not _is_ignored(text) and _looks_like_py_error(text):
                    browser.close()
                    return {
                        "example": example,
                        "status": "error",
                        "error": text[:300],
                        "runtime": "pyscript",
                        "phase": "after_quit",
                    }
            page.wait_for_timeout(100)

        log.poll()

        browser.close()

    if not results:
        return {
            "example": example,
            "status": "error",
            "error": "no EXAMPLE_RESULT after Ctrl+Q quit chord",
            "runtime": "pyscript",
            "phase": "after_quit",
            "console_tail": [m["text"][:120] for m in console_msgs[-8:]],
        }

    result = results[-1]
    # Prefer quit-injected ok; timer-based ok without quit is weaker.
    if result.get("status") == "ok" and not result.get("quit_injected"):
        result = dict(result)
        result["warning"] = "EXAMPLE_RESULT without quit_injected"
    return result


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__.strip(), file=sys.stderr)
        return 2
    url = argv[0]
    duration = 5.0
    timeout = 45.0
    i = 1
    while i < len(argv):
        if argv[i] == "--duration" and i + 1 < len(argv):
            duration = float(argv[i + 1])
            i += 2
        elif argv[i] == "--timeout" and i + 1 < len(argv):
            timeout = float(argv[i + 1])
            i += 2
        else:
            print(f"unknown arg: {argv[i]}", file=sys.stderr)
            return 2

    # CLI / pyscript.sh --autotest: always stream #log to stdout.
    result = run_autotest(url, duration_s=duration, timeout_s=timeout, stream_log=True)
    print("EXAMPLE_RESULT=" + json.dumps(result, separators=(",", ":")))
    return 0 if result.get("status") == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
