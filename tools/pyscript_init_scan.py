#!/usr/bin/env python3
"""Sequential PyScript scan: wait for PSDisplay init lines (or error) per example.

For each example in ``example_test_manifest.toml``:
  1. Load ``embed.html?...`` (no Ctrl+Q)
  2. Stream ``#log`` to stdout
  3. Succeed when all three lines appear::

       Initializing PSDisplay...
       PSDisplay: initialized.
       Runtime: timer_async=True.

  4. Fail on traceback / ImportError-style ``#log`` or pageerror
  5. After ``--timeout`` seconds (default 30), kill the page and move on

Usage:
  .venv/bin/python tools/pyscript_init_scan.py
  .venv/bin/python tools/pyscript_init_scan.py --only nano_gui_simpletest
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
import time
from typing import Any

REPO = Path(__file__).resolve().parents[1]
TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from example_test_kit import (  # noqa: E402
    ensure_pyscript_server,
    load_manifest,
    pyscript_embed_query,
)

TARGETS = (
    "Initializing PSDisplay...",
    "PSDisplay: initialized.",
    "Runtime: timer_async=True.",
)

_ERR_RE = re.compile(
    r"(?i)(traceback \(most recent call last\)|importerror:|modulenotfounderror:|"
    r"syntaxerror:|memoryerror:|typeerror:|attributeerror:|runtimeerror:|"
    r"oserror:|failed to install|EXAMPLE_RESULT=\{[^}]*\"status\":\"error\")"
)


def _scan_one(
    example_id: str,
    example_meta: dict,
    *,
    timeout_s: float,
    port: int,
    stream: bool,
) -> dict[str, Any]:
    from playwright.sync_api import sync_playwright

    query = pyscript_embed_query(example_id, example_meta)
    url = f"http://127.0.0.1:{port}/web/pyscript/embed.html?{query}"
    found = dict.fromkeys(TARGETS, False)
    log_lines: list[str] = []
    errors: list[str] = []
    t0 = time.monotonic()
    seen = ""

    def elapsed() -> float:
        return time.monotonic() - t0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        def on_console(msg) -> None:
            text = msg.text or ""
            if msg.type == "error" and text and text not in errors:
                errors.append(text[:300])
            if text.startswith("EXAMPLE_RESULT=") and '"status":"error"' in text:
                errors.append(text[:300])

        page.on("console", on_console)
        page.on(
            "pageerror",
            lambda exc: errors.append(str(exc)[:300]) if str(exc) not in errors else None,
        )

        try:
            page.goto(url, wait_until="load", timeout=int(min(timeout_s, 45) * 1000))
        except Exception as exc:
            browser.close()
            return {
                "example": example_id,
                "status": "error",
                "error": f"page.goto: {exc}",
                "elapsed_s": round(elapsed(), 2),
                "found": found,
            }

        deadline = time.monotonic() + timeout_s
        status = "timeout"
        detail = f"no init lines within {timeout_s:.0f}s"
        while time.monotonic() < deadline:
            try:
                text = (
                    page.evaluate(
                        "() => { const el = document.getElementById('log');"
                        " return el ? el.textContent : ''; }"
                    )
                    or ""
                )
            except Exception as exc:
                status = "error"
                detail = f"evaluate #log: {exc}"
                break

            if text != seen:
                chunk = text[len(seen) :] if text.startswith(seen) else text
                seen = text
                for line in chunk.splitlines():
                    if not line.strip():
                        continue
                    log_lines.append(line)
                    if stream:
                        print(f"  [{example_id}] {line}", flush=True)
                    for t in TARGETS:
                        if t in line:
                            found[t] = True
                    if _ERR_RE.search(line) and line not in errors:
                        errors.append(line[:300])

            if all(found.values()):
                status = "ok"
                detail = "all init lines seen"
                break
            if errors:
                status = "error"
                detail = errors[0]
                break
            page.wait_for_timeout(50)

        try:
            browser.close()
        except Exception:
            pass

    return {
        "example": example_id,
        "status": status,
        "error": None if status == "ok" else detail,
        "elapsed_s": round(elapsed(), 2),
        "found": found,
        "log_tail": log_lines[-8:],
        "url": url,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=float, default=30.0, help="per-example seconds")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--only", action="append", default=[], help="limit to example id(s)")
    parser.add_argument("--quiet-log", action="store_true", help="do not stream #log lines")
    parser.add_argument(
        "--json-out",
        type=Path,
        default=REPO / ".cursor" / "pyscript_init_scan.json",
        help="write full results JSON",
    )
    args = parser.parse_args(argv)

    _defaults, examples = load_manifest()
    names = sorted(examples)
    if args.only:
        want = set(args.only)
        names = [n for n in names if n in want]
        missing = want - set(names)
        if missing:
            print(f"unknown examples: {sorted(missing)}", file=sys.stderr)
            return 2

    ensure_pyscript_server(args.port)
    print(
        f"pyscript_init_scan: {len(names)} examples, timeout={args.timeout:.0f}s each\n",
        flush=True,
    )

    results: list[dict[str, Any]] = []
    counts = {"ok": 0, "error": 0, "timeout": 0}
    t_all = time.monotonic()

    for i, name in enumerate(names, 1):
        print(f"=== [{i}/{len(names)}] {name} ===", flush=True)
        row = _scan_one(
            name,
            examples[name],
            timeout_s=args.timeout,
            port=args.port,
            stream=not args.quiet_log,
        )
        results.append(row)
        counts[row["status"]] = counts.get(row["status"], 0) + 1
        mark = {"ok": "OK", "error": "ERR", "timeout": "TIMEOUT"}.get(row["status"], "?")
        extra = "" if row["status"] == "ok" else f" — {row.get('error')}"
        print(f"--> {mark} {name} ({row['elapsed_s']}s){extra}\n", flush=True)

    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "timeout_s": args.timeout,
        "counts": counts,
        "elapsed_s": round(time.monotonic() - t_all, 1),
        "results": results,
    }
    args.json_out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    print("--- summary ---", flush=True)
    print(
        f"ok={counts.get('ok', 0)} error={counts.get('error', 0)} "
        f"timeout={counts.get('timeout', 0)} "
        f"total={len(results)} wall={payload['elapsed_s']}s",
        flush=True,
    )
    print(f"json: {args.json_out}", flush=True)
    for row in results:
        if row["status"] != "ok":
            print(f"  {row['status']:7} {row['example']}: {row.get('error')}", flush=True)

    return 0 if counts.get("error", 0) == 0 and counts.get("timeout", 0) == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
