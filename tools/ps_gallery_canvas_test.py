#!/usr/bin/env python3
"""Gallery canvas verifier for micropython.html and pyodide.html loaders.

For every card in ``web/pyscript/index.html``, on each loader:

  1. Navigate, wait for Run, click Run
  2. Watch ``#display_canvas`` for non-blank pixels (JS sampler + CDP shots)
  3. Inject canvas clicks on interactive demos
  4. Save a screenshot under ``.cursor/pyscript_gallery_shots/``
  5. Abort immediately if console output implicates ``multimer``

Does **not** edit multimer. Prefer CDP screenshots when sync WASM may block
``page.evaluate`` (see ``.cursor/pyscript-troubleshooting.md``).

Usage:
  # server must already be up:  .venv/bin/python tools/serve.py
  .venv/bin/python tools/ps_gallery_canvas_test.py
  .venv/bin/python tools/ps_gallery_canvas_test.py --only pydisplay_demo paint
  .venv/bin/python tools/ps_gallery_canvas_test.py --loaders micropython
  .venv/bin/python tools/ps_gallery_canvas_test.py --limit 3
"""

from __future__ import annotations

import argparse
import base64
import json
import re
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

REPO = Path(__file__).resolve().parents[1]
INDEX = REPO / "web" / "pyscript" / "index.html"
DEFAULT_BASE = "http://127.0.0.1:8000/web/pyscript"
OUT_DIR = REPO / ".cursor" / "pyscript_gallery_shots"
RESULTS_JSON = REPO / ".cursor" / "pyscript_gallery_canvas_results.json"

# Names where we inject pointer clicks after paint (gallery interactive set).
INTERACTIVE = {
    "pydisplay_demo",
    "paint",
    "testris",
    "eventsys_simpletest",
    "eventsys_touch_test",
    "eventsys_encoder_test",
    "calc_graphics",
    "calc_widgets",
    "calc_lvgl",
    "tv_remote_menu",
    "joystick_list_select",
    "touch_gui_simpletest",
    "widgets_actions",
    "widgets_demo",
    "widgets_device_panel",
    "widgets_form_kitchen",
    "widgets_gauge_dash",
    "widgets_media_busy",
    "widgets_nav_tabs",
    "widgets_percent",
    "widgets_pickers",
    "widgets_settings",
    "widgets_sheets",
    "widgets_smartwatch",
    "scroll",
    "lv_test_timer",
}

# Console text that means stop the whole matrix (multimer implicated).
_MULTIMER_STOP = re.compile(
    r"(?i)\b(multimer|asynctimer|set_deadline_hook|schedule queue|"
    r"asyncio\.(?:sleep|get_event_loop|create_task)|"
    r"Timer\.(?:init|deinit)|"
    r"machine\.Timer)\b"
)

_IGNORE_ERR = (
    "Failed to execute 'fetch' on 'Window'",
    "net::ERR_",
    "ResizeObserver loop",
    "favicon",
)

_CANVAS_SAMPLER_JS = """
() => {
  if (window.__pyCanvasWatch) return 'already';
  const state = {
    samples: 0,
    painted: false,
    nonBlank: 0,
    lastUnique: 0,
    hashes: [],
    error: null,
  };
  window.__pyCanvasWatch = state;
  const hash = (data) => {
    let h = 2166136261;
    // stride sample for speed
    for (let i = 0; i < data.length; i += 64) {
      h ^= data[i];
      h = Math.imul(h, 16777619);
    }
    return h >>> 0;
  };
  const sample = () => {
    try {
      const c = document.getElementById('display_canvas');
      if (!c) return;
      const ctx = c.getContext('2d', { willReadFrequently: true });
      if (!ctx) return;
      const { width: w, height: h } = c;
      if (!w || !h) return;
      const img = ctx.getImageData(0, 0, w, h);
      const d = img.data;
      let nonBlank = 0;
      let r0 = d[0], g0 = d[1], b0 = d[2], a0 = d[3];
      let uniform = true;
      for (let i = 0; i < d.length; i += 16) {
        const a = d[i + 3];
        const r = d[i], g = d[i + 1], b = d[i + 2];
        if (a > 0 && (r | g | b) !== 0) nonBlank++;
        if (r !== r0 || g !== g0 || b !== b0 || a !== a0) uniform = false;
      }
      const hv = hash(d);
      state.samples += 1;
      state.nonBlank = nonBlank;
      if (nonBlank > 8 && !uniform) {
        state.painted = true;
      }
      if (!state.hashes.length || state.hashes[state.hashes.length - 1] !== hv) {
        state.hashes.push(hv);
        if (state.hashes.length > 12) state.hashes.shift();
        state.lastUnique = Date.now();
      }
    } catch (e) {
      state.error = String(e);
    }
  };
  sample();
  const tick = () => { sample(); requestAnimationFrame(tick); };
  requestAnimationFrame(tick);
  setInterval(sample, 250);
  return 'armed';
}
"""

_READ_WATCH_JS = """
() => {
  const s = window.__pyCanvasWatch || null;
  const c = document.getElementById('display_canvas');
  let direct = null;
  if (c) {
    try {
      const ctx = c.getContext('2d', { willReadFrequently: true });
      const img = ctx.getImageData(0, 0, c.width, c.height);
      const d = img.data;
      let nonBlank = 0;
      for (let i = 0; i < d.length; i += 16) {
        if (d[i+3] > 0 && (d[i] | d[i+1] | d[i+2]) !== 0) nonBlank++;
      }
      direct = { w: c.width, h: c.height, nonBlank };
    } catch (e) {
      direct = { error: String(e) };
    }
  }
  const log = document.getElementById('log');
  const status = document.getElementById('status');
  const btn = document.getElementById('run-btn');
  return {
    watch: s,
    direct,
    log: log ? log.textContent.slice(-2000) : '',
    status: status ? status.textContent : '',
    btn: btn ? { disabled: btn.disabled, text: btn.textContent } : null,
  };
}
"""


@dataclass
class CaseResult:
    example: str
    loader: str
    query: str
    status: str
    painted: bool = False
    activity: bool = False
    clicks_injected: int = 0
    screenshot: str | None = None
    error: str | None = None
    console_errors: list[str] = field(default_factory=list)
    log_tail: str = ""
    elapsed_s: float = 0.0
    multimer_hit: bool = False
    notes: list[str] = field(default_factory=list)


def gallery_entries() -> list[dict[str, str]]:
    html = INDEX.read_text(encoding="utf-8")
    hrefs = re.findall(r'<a class="card" href="(micropython\.html\?[^"]+)">', html)
    out: list[dict[str, str]] = []
    seen: set[str] = set()
    for href in hrefs:
        q = href.split("?", 1)[1]
        qs = parse_qs(q)
        name = (qs.get("modules") or qs.get("manifests") or ["?"])[0].split(",")[0]
        if name in seen:
            continue
        seen.add(name)
        out.append({"name": name, "query": q, "href": href})
    return out


def _png_nonblank_stats(png_bytes: bytes) -> dict[str, Any]:
    """Offline paint heuristic from a full-page PNG (no JS)."""
    try:
        from PIL import Image
        import io

        im = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
        # Sample center band where the 320x480 device canvas usually sits.
        w, h = im.size
        # device column is leftish on desktop layout
        left = int(w * 0.05)
        right = int(w * 0.55)
        top = int(h * 0.12)
        bottom = int(h * 0.85)
        crop = im.crop((left, top, max(left + 10, right), max(top + 10, bottom)))
        # Prefer get_flattened_data (Pillow 14+); fall back for older Pillow.
        flat_fn = getattr(crop, "get_flattened_data", None)
        if flat_fn is not None:
            flat = list(flat_fn())
            px = [tuple(flat[i : i + 4]) for i in range(0, len(flat), 4)]
        else:
            px = list(crop.getdata())
        step = max(1, len(px) // 8000)
        non_blank = 0
        colors: set[tuple[int, int, int]] = set()
        for i in range(0, len(px), step):
            r, g, b, a = px[i]
            if a < 8:
                continue
            # ignore near-white page chrome and near-black empty canvas
            if r > 245 and g > 245 and b > 245:
                continue
            if r < 8 and g < 8 and b < 8:
                continue
            non_blank += 1
            colors.add((r // 16, g // 16, b // 16))
        return {
            "non_blank_samples": non_blank,
            "unique_buckets": len(colors),
            "painted": non_blank >= 40 and len(colors) >= 2,
            "size": [w, h],
        }
    except Exception as e:
        return {"error": str(e), "painted": False}


def run_case(
    *,
    base: str,
    loader: str,
    entry: dict[str, str],
    soak_s: float,
    ready_timeout_s: float,
    out_dir: Path,
    headless: bool,
) -> CaseResult:
    from playwright.sync_api import sync_playwright

    name = entry["name"]
    query = entry["query"]
    url = f"{base}/{loader}.html?{query}"
    t0 = time.monotonic()
    res = CaseResult(example=name, loader=loader, query=query, status="unknown")
    console: list[str] = []
    page_errors: list[str] = []

    def elapsed() -> float:
        return time.monotonic() - t0

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless,
            args=[
                "--no-sandbox",
                "--disable-gpu",
                "--enable-features=SharedArrayBuffer",
            ],
        )
        ctx = browser.new_context(
            viewport={"width": 1100, "height": 900},
            device_scale_factor=1,
        )
        page = ctx.new_page()
        cdp = ctx.new_cdp_session(page)
        cdp.send("Runtime.enable")
        cdp.send("Console.enable")

        def on_console_api(params: dict) -> None:
            args = params.get("args", [])
            texts = []
            for a in args:
                if a.get("type") == "string":
                    texts.append(a.get("value", ""))
                else:
                    texts.append(str(a.get("value", a.get("description", "?"))))
            text = " ".join(texts)
            console.append(text)
            if _MULTIMER_STOP.search(text) and not any(s in text for s in _IGNORE_ERR):
                # Only flag if it looks like an error / traceback context
                low = text.lower()
                if any(
                    k in low
                    for k in (
                        "error",
                        "traceback",
                        "exception",
                        "failed",
                        "not available",
                        "attributeerror",
                        "typeerror",
                        "runtimeerror",
                    )
                ):
                    res.multimer_hit = True
                    res.notes.append(f"multimer console: {text[:240]}")

        def on_exception(params: dict) -> None:
            exc = params.get("exceptionDetails", {})
            text = exc.get("text", "") + " " + str(
                (exc.get("exception") or {}).get("description", "")
            )
            page_errors.append(text)
            if _MULTIMER_STOP.search(text):
                res.multimer_hit = True
                res.notes.append(f"multimer exception: {text[:240]}")

        cdp.on("Runtime.consoleAPICalled", on_console_api)
        cdp.on("Runtime.exceptionThrown", on_exception)

        def on_page_error(err) -> None:
            text = str(err)
            page_errors.append(text)
            if _MULTIMER_STOP.search(text):
                res.multimer_hit = True
                res.notes.append(f"multimer pageerror: {text[:240]}")

        page.on("pageerror", on_page_error)

        try:
            page.goto(url, timeout=20000, wait_until="domcontentloaded")
        except Exception as e:
            res.status = "nav_error"
            res.error = str(e)
            res.elapsed_s = elapsed()
            browser.close()
            return res

        # Arm canvas watcher before Run (JS free).
        try:
            page.evaluate(_CANVAS_SAMPLER_JS)
        except Exception as e:
            res.notes.append(f"sampler arm failed: {e}")

        # Wait for Run enabled
        deadline = time.monotonic() + ready_timeout_s
        ready = False
        while time.monotonic() < deadline:
            try:
                st = page.evaluate(
                    "() => { const b=document.getElementById('run-btn');"
                    " return b ? {d:b.disabled,t:b.textContent} : null; }"
                )
                if st and not st.get("d"):
                    ready = True
                    break
            except Exception:
                pass
            page.wait_for_timeout(250)
        if not ready:
            res.status = "runtime_not_ready"
            res.error = "Run button never enabled"
            _save_cdp_shot(cdp, out_dir / f"{loader}__{name}__noready.png", res)
            res.elapsed_s = elapsed()
            browser.close()
            return res

        try:
            page.click("#run-btn", timeout=5000)
        except Exception as e:
            res.status = "run_click_failed"
            res.error = str(e)
            res.elapsed_s = elapsed()
            browser.close()
            return res

        # Soak: prefer Playwright waits (keeps CDP alive). Periodically try watch read.
        painted = False
        activity = False
        last_hashes = 0
        soak_deadline = time.monotonic() + soak_s
        while time.monotonic() < soak_deadline:
            if res.multimer_hit:
                break
            page.wait_for_timeout(400)
            try:
                snap = page.evaluate(_READ_WATCH_JS)
                watch = (snap or {}).get("watch") or {}
                direct = (snap or {}).get("direct") or {}
                if watch.get("painted") or (direct.get("nonBlank") or 0) > 8:
                    painted = True
                hashes = watch.get("hashes") or []
                if len(hashes) > last_hashes:
                    if last_hashes:
                        activity = True
                    last_hashes = len(hashes)
                res.log_tail = (snap or {}).get("log") or ""
                # Fail fast on Run failed in log
                if "Run failed:" in res.log_tail:
                    res.status = "run_failed"
                    res.error = res.log_tail.strip().splitlines()[-1][:300]
                    break
            except Exception as e:
                # Likely main-thread blocked — keep soaking; CDP shot later.
                res.notes.append(f"eval blocked: {type(e).__name__}")

        # Interactive clicks (best-effort; may no-op if main thread blocked)
        clicks = 0
        if name in INTERACTIVE and res.status not in ("run_failed",):
            for x, y in ((40, 40), (160, 240), (280, 400), (100, 100), (200, 300)):
                try:
                    page.locator("#display_canvas").click(
                        position={"x": x, "y": y}, timeout=1500, force=True
                    )
                    clicks += 1
                    page.wait_for_timeout(200)
                except Exception:
                    break
            res.clicks_injected = clicks
            # brief post-click soak for paint/activity
            page.wait_for_timeout(800)
            try:
                snap = page.evaluate(_READ_WATCH_JS)
                watch = (snap or {}).get("watch") or {}
                if watch.get("painted"):
                    painted = True
                if len(watch.get("hashes") or []) > last_hashes:
                    activity = True
                res.log_tail = (snap or {}).get("log") or res.log_tail
            except Exception:
                pass

        shot_path = out_dir / f"{loader}__{name}.png"
        png = _save_cdp_shot(cdp, shot_path, res)
        if png:
            stats = _png_nonblank_stats(png)
            res.notes.append(f"png_stats={stats}")
            if stats.get("painted"):
                painted = True

        # Console / log error harvest
        for text in console + page_errors:
            if _looks_error(text):
                res.console_errors.append(text[:400])
        if _looks_error(res.log_tail):
            res.console_errors.append("log:" + res.log_tail.strip()[-400:])

        res.painted = painted
        res.activity = activity
        if res.multimer_hit:
            res.status = "multimer_issue"
        elif res.status == "run_failed":
            pass
        elif painted:
            res.status = "ok_painted"
        elif res.console_errors:
            res.status = "error_no_paint"
            res.error = res.console_errors[0][:300]
        else:
            res.status = "no_paint"
            res.error = "canvas stayed blank / no detectable pixels"

        res.elapsed_s = elapsed()
        browser.close()
        return res


def _looks_error(text: str) -> bool:
    if not text:
        return False
    if any(s in text for s in _IGNORE_ERR):
        return False
    return bool(
        re.search(
            r"(?i)(traceback|error:|exception|run failed|importerror|"
            r"modulenotfounderror|attributeerror|typeerror|runtimeerror)",
            text,
        )
    )


def _save_cdp_shot(cdp, path: Path, res: CaseResult) -> bytes | None:
    path.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(4):
        try:
            r = cdp.send("Page.captureScreenshot", {"format": "png"})
            data = base64.b64decode(r.get("data", ""))
            path.write_bytes(data)
            res.screenshot = str(path.relative_to(REPO))
            return data
        except Exception as e:
            res.notes.append(f"shot attempt {attempt+1}: {e}")
            time.sleep(0.15)
    return None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base", default=DEFAULT_BASE)
    ap.add_argument(
        "--loaders",
        default="micropython,pyodide",
        help="comma list: micropython,pyodide",
    )
    ap.add_argument("--only", nargs="*", help="example name(s) to include")
    ap.add_argument("--limit", type=int, default=0, help="max examples (0=all)")
    ap.add_argument("--soak", type=float, default=8.0, help="seconds after Run")
    ap.add_argument("--ready-timeout", type=float, default=45.0)
    ap.add_argument("--out-dir", type=Path, default=OUT_DIR)
    ap.add_argument("--results", type=Path, default=RESULTS_JSON)
    ap.add_argument("--headed", action="store_true")
    ap.add_argument(
        "--continue-on-multimer",
        action="store_true",
        help="do not abort matrix on multimer hit (default: abort)",
    )
    args = ap.parse_args(argv)

    entries = gallery_entries()
    if args.only:
        want = set(args.only)
        entries = [e for e in entries if e["name"] in want]
    if args.limit and args.limit > 0:
        entries = entries[: args.limit]

    loaders = [x.strip() for x in args.loaders.split(",") if x.strip()]
    args.out_dir.mkdir(parents=True, exist_ok=True)

    print(
        f"Gallery canvas test: {len(entries)} examples × {loaders} "
        f"(soak={args.soak}s) → {args.out_dir}",
        flush=True,
    )

    results: list[CaseResult] = []
    stopped_early = False
    for entry in entries:
        for loader in loaders:
            print(f"\n=== {loader} :: {entry['name']} ===", flush=True)
            r = run_case(
                base=args.base.rstrip("/"),
                loader=loader,
                entry=entry,
                soak_s=args.soak,
                ready_timeout_s=args.ready_timeout,
                out_dir=args.out_dir,
                headless=not args.headed,
            )
            results.append(r)
            flag = "PAINT" if r.painted else "BLANK"
            print(
                f"→ {r.status} [{flag}] clicks={r.clicks_injected} "
                f"{r.elapsed_s:.1f}s shot={r.screenshot}",
                flush=True,
            )
            if r.error:
                print(f"  error: {r.error[:200]}", flush=True)
            if r.multimer_hit:
                print("!!! MULTIMER ISSUE DETECTED — stopping matrix", flush=True)
                if not args.continue_on_multimer:
                    stopped_early = True
                    break
        if stopped_early:
            break

    payload = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "stopped_early": stopped_early,
        "counts": {
            "total": len(results),
            "ok_painted": sum(1 for r in results if r.status == "ok_painted"),
            "no_paint": sum(1 for r in results if r.status == "no_paint"),
            "errors": sum(
                1
                for r in results
                if r.status
                not in ("ok_painted", "no_paint", "multimer_issue")
            ),
            "multimer": sum(1 for r in results if r.multimer_hit),
        },
        "results": [asdict(r) for r in results],
    }
    args.results.parent.mkdir(parents=True, exist_ok=True)
    args.results.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"\nWrote {args.results}", flush=True)
    print(json.dumps(payload["counts"], indent=2), flush=True)

    if stopped_early:
        return 2
    # non-zero if any blank/error
    bad = [r for r in results if r.status != "ok_painted"]
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
