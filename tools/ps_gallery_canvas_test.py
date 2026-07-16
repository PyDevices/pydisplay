#!/usr/bin/env python3
"""Gallery canvas verifier for micropython.html and pyodide.html loaders.

For every card in ``web/pyscript/index.html``, on each loader:

  1. Navigate, wait for Run, click Run (via setTimeout — does not wait on handler)
  2. Watch the page via CDP ``Page.startScreencast`` (survives sync WASM loops;
     ``Page.captureScreenshot`` can hang after ``run_forever``)
  3. Inject canvas clicks on interactive demos
  4. Save a screenshot under the out-dir
  5. Abort immediately if console output implicates ``multimer``

Hard rule: each case is killed if it exceeds ``--case-timeout`` (default **15s**).
After Run, never call ``page.evaluate`` / ``captureScreenshot`` on sync-prone demos.
Does **not** edit multimer.

Paint notes:
  - ``paint`` is mostly black with a color strip across the top — black is valid;
    compare against a pre-Run blank baseline.
  - ``testris`` shows a splash first (disable via ``SPLASH_ENABLED`` /
    ``pydisplay_test_mode``); splash still counts as painted.

Usage:
  .venv/bin/python tools/serve.py
  .venv/bin/python tools/ps_gallery_canvas_test.py
  .venv/bin/python tools/ps_gallery_canvas_test.py --only testris paint
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import multiprocessing as mp
import os
import re
import sys
import tempfile
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
INDEX = REPO / "web" / "pyscript" / "index.html"
DEFAULT_BASE = "http://127.0.0.1:8000/web/pyscript"
OUT_DIR = REPO / ".cursor" / "pyscript_gallery_shots"
RESULTS_JSON = REPO / ".cursor" / "pyscript_gallery_canvas_results.json"
DEFAULT_CASE_TIMEOUT_S = 15.0

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

_LOG_WATCH_JS = """
() => {
  const log = document.getElementById('log');
  if (!log || log.__pyLogWatch) return 'skip';
  log.__pyLogWatch = true;
  let last = '';
  const dump = () => {
    const t = log.textContent || '';
    if (t === last) return;
    const chunk = t.startsWith(last) ? t.slice(last.length) : t;
    last = t;
    if (chunk.trim()) console.log('[#log] ' + chunk.slice(-800));
  };
  new MutationObserver(dump).observe(log, {
    childList: true, characterData: true, subtree: true
  });
  setInterval(dump, 300);
  return 'armed';
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
    """Collect gallery demos with per-runtime loader queries from url_maker."""
    scripts = REPO / "scripts"
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))
    from gallery_generator import discover

    out: list[dict[str, object]] = []
    for ex in discover():
        if not ex.in_gallery:
            continue
        qs = ex.loader_queries()
        queries = {rt: q.lstrip("?") for rt, q in qs.items()}
        out.append(
            {
                "name": ex.name,
                "query": queries["micropython"],
                "queries": queries,
                "href": f"micropython.html?{queries['micropython']}",
            }
        )
    return out


def _png_digest(png_bytes: bytes) -> str:
    return hashlib.sha1(png_bytes).hexdigest()[:16]


def _crop_png(png_bytes: bytes, box: dict[str, float] | None) -> bytes | None:
    if not box:
        return None
    try:
        import io

        from PIL import Image

        im = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
        x, y = int(box["x"]), int(box["y"])
        w, h = int(box["w"]), int(box["h"])
        if w < 8 or h < 8:
            return None
        x2, y2 = min(im.width, x + w), min(im.height, y + h)
        x, y = max(0, x), max(0, y)
        if x2 <= x or y2 <= y:
            return None
        buf = io.BytesIO()
        im.crop((x, y, x2, y2)).save(buf, format="PNG")
        return buf.getvalue()
    except Exception:
        return None


def _iter_rgba(im) -> list[tuple[int, int, int, int]]:
    flat_fn = getattr(im, "get_flattened_data", None)
    if flat_fn is not None:
        flat = list(flat_fn())
        if flat and isinstance(flat[0], tuple):
            return [(int(p[0]), int(p[1]), int(p[2]), int(p[3])) for p in flat]
        return [
            (int(flat[i]), int(flat[i + 1]), int(flat[i + 2]), int(flat[i + 3]))
            for i in range(0, len(flat), 4)
        ]
    return [tuple(p) for p in im.getdata()]  # type: ignore[misc]


def _canvas_paint_stats(
    png_bytes: bytes,
    *,
    baseline: bytes | None = None,
) -> dict[str, Any]:
    """Black canvases with a color strip (paint) still count as painted."""
    try:
        import io

        from PIL import Image

        im = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
        w, h = im.size
        px = _iter_rgba(im)
        step = max(1, len(px) // 12000)
        colors: set[tuple[int, int, int, int]] = set()
        opaque = 0
        for i in range(0, len(px), step):
            r, g, b, a = px[i]
            colors.add((r // 8, g // 8, b // 8, 1 if a > 8 else 0))
            if a > 8 and (r | g | b) != 0:
                opaque += 1
        digest = _png_digest(png_bytes)
        base_digest = _png_digest(baseline) if baseline else None
        changed = bool(baseline) and digest != base_digest
        painted = changed or len(colors) >= 3 or opaque >= 20
        return {
            "painted": painted,
            "changed_from_baseline": changed,
            "unique_buckets": len(colors),
            "opaque_samples": opaque,
            "digest": digest,
            "baseline_digest": base_digest,
            "size": [w, h],
        }
    except Exception as e:
        return {"error": str(e), "painted": False}


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


def _flag_multimer(text: str, res: CaseResult, prefix: str) -> None:
    if not _MULTIMER_STOP.search(text):
        return
    if any(s in text for s in _IGNORE_ERR):
        return
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
        res.notes.append(f"{prefix}: {text[:240]}")


def run_case(
    *,
    base: str,
    loader: str,
    entry: dict[str, str],
    soak_s: float,
    ready_timeout_s: float,
    out_dir: Path,
    headless: bool,
    case_timeout_s: float = DEFAULT_CASE_TIMEOUT_S,
) -> CaseResult:
    from playwright.sync_api import sync_playwright

    name = entry["name"]
    queries = entry.get("queries") or {}
    query = queries.get(loader) or entry["query"]
    url = f"{base}/{loader}.html?{query}"
    t0 = time.monotonic()
    hard_deadline = t0 + max(3.0, case_timeout_s - 0.7)
    res = CaseResult(example=name, loader=loader, query=query, status="unknown")
    console: list[str] = []
    page_errors: list[str] = []
    frames: list[bytes] = []

    def elapsed() -> float:
        return time.monotonic() - t0

    def remaining() -> float:
        return hard_deadline - time.monotonic()

    # Never use the context-manager form — __exit__ hangs when WASM blocks.
    pw = sync_playwright().start()
    browser = pw.chromium.launch(
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
    page.set_default_timeout(min(4000, int(case_timeout_s * 1000)))
    cdp = ctx.new_cdp_session(page)
    cdp.send("Runtime.enable")
    cdp.send("Console.enable")
    cdp.send("Page.enable")

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
        _flag_multimer(text, res, "multimer console")

    def on_exception(params: dict) -> None:
        exc = params.get("exceptionDetails", {})
        text = exc.get("text", "") + " " + str(
            (exc.get("exception") or {}).get("description", "")
        )
        page_errors.append(text)
        _flag_multimer(text, res, "multimer exception")

    def on_frame(params: dict) -> None:
        try:
            data = base64.b64decode(params.get("data", ""))
            if data:
                frames.append(data)
            cdp.send(
                "Page.screencastFrameAck",
                {"sessionId": params.get("sessionId")},
            )
        except Exception:
            pass

    cdp.on("Runtime.consoleAPICalled", on_console_api)
    cdp.on("Runtime.exceptionThrown", on_exception)
    cdp.on("Page.screencastFrame", on_frame)

    def on_page_error(err) -> None:
        text = str(err)
        page_errors.append(text)
        _flag_multimer(text, res, "multimer pageerror")

    page.on("pageerror", on_page_error)

    # Screencast BEFORE Run — frames keep arriving after sync WASM starts.
    cdp.send(
        "Page.startScreencast",
        {"format": "png", "everyNthFrame": 1, "quality": 70},
    )

    nav_ms = int(min(6000, max(2000, remaining() * 1000)))
    try:
        page.goto(url, timeout=nav_ms, wait_until="domcontentloaded")
    except Exception as e:
        res.status = "nav_error"
        res.error = str(e)
        res.elapsed_s = elapsed()
        return res

    try:
        page.evaluate(_LOG_WATCH_JS)
    except Exception as e:
        res.notes.append(f"log watch: {e}")

    ready_budget = min(ready_timeout_s, max(1.0, remaining() - soak_s - 2.0))
    deadline = time.monotonic() + ready_budget
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
        page.wait_for_timeout(150)
    if not ready:
        res.status = "runtime_not_ready"
        res.error = "Run button never enabled"
        res.elapsed_s = elapsed()
        return res

    canvas_box = None
    try:
        canvas_box = page.evaluate(
            "() => { const c=document.getElementById('display_canvas');"
            " if(!c) return null;"
            " const r=c.getBoundingClientRect();"
            " return {x:r.x,y:r.y,w:r.width,h:r.height}; }"
        )
    except Exception as e:
        res.notes.append(f"canvas box: {e}")

    # Drop stale artifacts.
    for stale in out_dir.glob(f"{loader}__{name}*"):
        try:
            stale.unlink()
        except Exception:
            pass

    shot_path = out_dir / f"{loader}__{name}.png"
    canvas_shot_path = out_dir / f"{loader}__{name}__canvas.png"

    # Baseline = last pre-Run screencast frame, cropped to canvas.
    baseline_crop: bytes | None = None
    page.wait_for_timeout(200)
    if frames and canvas_box:
        baseline_crop = _crop_png(frames[-1], canvas_box)

    try:
        page.evaluate(
            """() => {
              const b = document.getElementById('run-btn');
              if (!b || b.disabled) throw new Error('run not ready');
              setTimeout(() => b.click(), 0);
              return true;
            }"""
        )
    except Exception as e:
        res.status = "run_click_failed"
        res.error = str(e)
        res.elapsed_s = elapsed()
        return res

    # ---- After Run: pump screencast only (no captureScreenshot / evaluate) ----
    painted = False
    activity = False
    prev_digest: str | None = None
    last_stats: dict = {}
    frames_at_run = len(frames)

    def _consider(full_png: bytes) -> None:
        nonlocal painted, activity, prev_digest, last_stats
        crop = _crop_png(full_png, canvas_box) or full_png
        stats = _canvas_paint_stats(crop, baseline=baseline_crop)
        last_stats = stats
        if stats.get("painted"):
            painted = True
        digest = stats.get("digest") or _png_digest(full_png)
        if prev_digest is not None and digest != prev_digest:
            activity = True
        prev_digest = digest

    soak_budget = min(soak_s, max(1.0, remaining() - 1.5))
    soak_deadline = time.monotonic() + soak_budget
    last_seen = frames_at_run
    splash_poked = False
    while time.monotonic() < soak_deadline and remaining() > 1.2:
        if res.multimer_hit:
            break
        # wait_for_timeout pumps CDP screencast events (time.sleep does not).
        page.wait_for_timeout(200)
        if len(frames) > last_seen:
            for fr in frames[last_seen:]:
                _consider(fr)
                # Persist latest frame continuously for timeout recovery.
                shot_path.write_bytes(fr)
            last_seen = len(frames)
            if painted:
                break
        if (
            name == "testris"
            and not splash_poked
            and last_seen > frames_at_run + 2
        ):
            splash_poked = True
            try:
                cdp.send(
                    "Input.dispatchKeyEvent",
                    {
                        "type": "keyDown",
                        "key": " ",
                        "code": "Space",
                        "windowsVirtualKeyCode": 32,
                    },
                )
                cdp.send(
                    "Input.dispatchKeyEvent",
                    {
                        "type": "keyUp",
                        "key": " ",
                        "code": "Space",
                        "windowsVirtualKeyCode": 32,
                    },
                )
            except Exception:
                pass

    clicks = 0
    if name in INTERACTIVE and canvas_box and remaining() > 1.0:
        bx, by = float(canvas_box["x"]), float(canvas_box["y"])
        bw = float(canvas_box["w"]) or 320.0
        bh = float(canvas_box["h"]) or 480.0
        points = (
            ((0.06, 0.04), (0.18, 0.04), (0.50, 0.35), (0.65, 0.50), (0.40, 0.60))
            if name == "paint"
            else ((0.12, 0.08), (0.5, 0.5), (0.88, 0.83), (0.3, 0.2), (0.62, 0.62))
        )
        for fx, fy in points:
            if remaining() < 0.8:
                break
            cx, cy = bx + fx * bw, by + fy * bh
            try:
                cdp.send(
                    "Input.dispatchMouseEvent",
                    {
                        "type": "mousePressed",
                        "x": cx,
                        "y": cy,
                        "button": "left",
                        "clickCount": 1,
                    },
                )
                cdp.send(
                    "Input.dispatchMouseEvent",
                    {
                        "type": "mouseReleased",
                        "x": cx,
                        "y": cy,
                        "button": "left",
                        "clickCount": 1,
                    },
                )
                clicks += 1
            except Exception as e:
                res.notes.append(f"cdp click: {e}")
                break
        res.clicks_injected = clicks
        page.wait_for_timeout(300)
        if len(frames) > last_seen:
            for fr in frames[last_seen:]:
                _consider(fr)
            last_seen = len(frames)

    if frames:
        shot_path.write_bytes(frames[-1])
        try:
            res.screenshot = str(shot_path.relative_to(REPO))
        except ValueError:
            res.screenshot = str(shot_path)
        crop = _crop_png(frames[-1], canvas_box)
        if crop:
            canvas_shot_path.write_bytes(crop)
            _consider(frames[-1])
        res.notes.append(f"canvas_stats={last_stats}")
        res.notes.append(f"screencast_frames={len(frames)}")

    for text in console + page_errors:
        if text.startswith("[#log]"):
            res.log_tail = (res.log_tail + "\n" + text[6:]).strip()[-2000:]
        if _looks_error(text):
            res.console_errors.append(text[:400])
    if _looks_error(res.log_tail):
        res.console_errors.append("log:" + res.log_tail.strip()[-400:])
        if "Run failed:" in res.log_tail and res.status == "unknown":
            res.status = "run_failed"
            res.error = res.log_tail.strip().splitlines()[-1][:300]

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
    return res


def _case_worker(result_path: str, kwargs: dict) -> None:
    try:
        r = run_case(**kwargs)
        payload = asdict(r)
    except Exception as e:
        entry = kwargs.get("entry") or {}
        payload = asdict(
            CaseResult(
                example=entry.get("name", "?"),
                loader=kwargs.get("loader", "?"),
                query=entry.get("query", ""),
                status="worker_crash",
                error=str(e),
            )
        )
    try:
        Path(result_path).write_text(json.dumps(payload), encoding="utf-8")
    except Exception:
        pass
    os._exit(0)


def run_case_hard_timeout(
    *,
    case_timeout_s: float,
    **kwargs,
) -> CaseResult:
    ctx = mp.get_context("spawn")
    kwargs = dict(kwargs)
    kwargs["case_timeout_s"] = case_timeout_s
    kwargs["out_dir"] = Path(kwargs["out_dir"])
    tmp = tempfile.NamedTemporaryFile(prefix="ps_gallery_", suffix=".json", delete=False)
    result_path = tmp.name
    tmp.close()
    proc = ctx.Process(target=_case_worker, args=(result_path, kwargs))
    t0 = time.monotonic()
    proc.start()
    proc.join(timeout=case_timeout_s)

    def _load_result() -> CaseResult | None:
        try:
            data = json.loads(Path(result_path).read_text(encoding="utf-8"))
            Path(result_path).unlink(missing_ok=True)
            return CaseResult(**data)
        except Exception:
            return None

    if proc.is_alive():
        proc.kill()
        proc.join(timeout=2)
        loaded = _load_result()
        if loaded is not None:
            loaded.notes = list(loaded.notes) + [
                "parent hit case-timeout after child wrote result"
            ]
            loaded.elapsed_s = time.monotonic() - t0
            return loaded
        entry = kwargs["entry"]
        out_dir = Path(kwargs["out_dir"])
        loader = kwargs["loader"]
        name = entry["name"]
        shot = out_dir / f"{loader}__{name}.png"
        painted = False
        notes = ["case exceeded --case-timeout; process killed"]
        if shot.exists():
            try:
                crop = _crop_png(
                    shot.read_bytes(),
                    {"x": 0.04 * 1100, "y": 0.25 * 900, "w": 0.36 * 1100, "h": 0.67 * 900},
                )
                if crop:
                    stats = _canvas_paint_stats(crop)
                    notes.append(f"timeout_canvas_stats={stats}")
                    painted = bool(stats.get("painted"))
            except Exception as e:
                notes.append(f"timeout analyze: {e}")
        return CaseResult(
            example=name,
            loader=loader,
            query=entry["query"],
            status="ok_painted" if painted else "timeout",
            painted=painted,
            error=None if painted else f"hard kill after {case_timeout_s:.0f}s",
            screenshot=str(shot) if shot.exists() else None,
            elapsed_s=time.monotonic() - t0,
            notes=notes,
        )

    loaded = _load_result()
    if loaded is not None:
        return loaded
    entry = kwargs["entry"]
    return CaseResult(
        example=entry["name"],
        loader=kwargs["loader"],
        query=entry["query"],
        status="worker_no_result",
        error="child exited without result file",
        elapsed_s=time.monotonic() - t0,
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base", default=DEFAULT_BASE)
    ap.add_argument("--loaders", default="micropython,pyodide")
    ap.add_argument("--only", nargs="*", help="example name(s) to include")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument(
        "--case-timeout",
        type=float,
        default=DEFAULT_CASE_TIMEOUT_S,
        help="hard per-case wall-clock kill (default 15s)",
    )
    ap.add_argument("--soak", type=float, default=3.5)
    ap.add_argument("--ready-timeout", type=float, default=8.0)
    ap.add_argument("--out-dir", type=Path, default=OUT_DIR)
    ap.add_argument("--results", type=Path, default=RESULTS_JSON)
    ap.add_argument("--headed", action="store_true")
    ap.add_argument("--continue-on-multimer", action="store_true")
    ap.add_argument("--no-subprocess", action="store_true")
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
        f"(case-timeout={args.case_timeout:.0f}s soak={args.soak}s) → {args.out_dir}",
        flush=True,
    )

    results: list[CaseResult] = []
    stopped_early = False
    for entry in entries:
        for loader in loaders:
            print(f"\n=== {loader} :: {entry['name']} ===", flush=True)
            kwargs = dict(
                base=args.base.rstrip("/"),
                loader=loader,
                entry=entry,
                soak_s=args.soak,
                ready_timeout_s=args.ready_timeout,
                out_dir=args.out_dir,
                headless=not args.headed,
                case_timeout_s=args.case_timeout,
            )
            if args.no_subprocess:
                r = run_case(**kwargs)
            else:
                r = run_case_hard_timeout(**kwargs)
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
        "case_timeout_s": args.case_timeout,
        "stopped_early": stopped_early,
        "counts": {
            "total": len(results),
            "ok_painted": sum(1 for r in results if r.status == "ok_painted"),
            "no_paint": sum(1 for r in results if r.status == "no_paint"),
            "timeout": sum(1 for r in results if r.status == "timeout"),
            "errors": sum(
                1
                for r in results
                if r.status
                not in ("ok_painted", "no_paint", "multimer_issue", "timeout")
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
    bad = [r for r in results if r.status != "ok_painted"]
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
