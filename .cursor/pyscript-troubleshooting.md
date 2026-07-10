# PyScript troubleshooting (agents)

How to investigate PyScript / MicroPython-WASM issues in this repo — especially
when **multimer**, timers, or sync loops are involved. Prefer evidence from a
running browser over guessing from source alone.

Related: [PyScript local development](../docs/guides/pyscript.md),
[PyScript asyncio](../docs/guides/pyscript-asyncio.md),
[multimer deadline hooks](../docs/concepts/multimer.md#development--troubleshooting--deadline-hooks),
[example runtimes](example-runtimes.md),
[`.cursor/rules/pyscript-browser-verify.mdc`](rules/pyscript-browser-verify.mdc).

## Pages and servers

| Page | Role |
|------|------|
| `web/pyscript/embed.html` | **Dev / automation** — auto-imports entry; supports `?autotest=1&duration=N` |
| `web/pyscript/load.html` | **Production gallery** — Run-gated; no autotest harness |
| `tools/serve.py` | Local server with COI headers (`COOP`/`COEP`) on port **8000** |

Always serve from repo root (`python tools/serve.py`). Confirm
`http://127.0.0.1:8000/web/pyscript/embed.html` returns 200 before probing.

Query params:

- `?modules=name` — single-file example under `src/examples/name.py`
- `?manifests=name` — package / MIP manifest (`web/pyscript/name.json`)
- `?autotest=1&duration=5` — matrix harness (embed only)
- `?debug=1` — show the `#log` console panel on embed

Wrong `modules=` vs `manifests=` yields import/`mip` 404s — check for a
matching `.json` under `web/pyscript/` before assuming a library bug.

## Choose a browser tool

| Tool | Use when |
|------|----------|
| **Playwright** (headless Chromium) | Default for hangs, matrix cells, console capture, reproducible probes |
| **Cursor Browser Tab MCP** | Brad should *see* the page; light UI checks |
| **`tools/example_test_kit.py --only-runtime pyscript`** | Full or scoped smoke matrix (uses Playwright internally) |

Install once: `.venv/bin/pip install -r requirements-dev.txt` and
`.venv/bin/playwright install chromium`.

### Critical: main-thread blocking

MicroPython WASM runs on the browser **main thread**.

- Sync `time.sleep_ms` / `multimer.sleep_ms` on this port **do not yield** to the
  JS event loop (unlike `await asyncio.sleep` / `await multimer.sleep_ms` in an
  async task).
- While Python is in a sync sleep or a tight `while True` with no await, **JS
  timers do not run**, and Playwright **`page.evaluate()`**, Cursor
  **`browser_take_screenshot`**, and similar round-trips often **hang**.
- Console / CDP messages can still arrive. Prefer **listening** over evaluating.

If the IDE browser tab wedges, kill it and switch to Playwright with a hard
process timeout.

## Playwright helpers in `tools/`

| Script | Purpose |
|--------|---------|
| [`ps_debug.py`](../tools/ps_debug.py) | Headless navigate + CDP console/log/network; good first probe |
| [`ps_screenshot.py`](../tools/ps_screenshot.py) | Wait N seconds, screenshot; CDP console only (avoids `evaluate` during sleep) |
| [`ps_shot.py`](../tools/ps_shot.py) | Screenshot with a hard kill timer if the browser stalls |

```bash
# Server must already be up
.venv/bin/python tools/ps_debug.py \
  'http://127.0.0.1:8000/web/pyscript/embed.html?modules=calculator&autotest=1&duration=5' 20

.venv/bin/python tools/ps_shot.py \
  'http://127.0.0.1:8000/web/pyscript/embed.html?manifests=tiny_toasters' 6 /tmp/ps.png
```

Patterns that work well in ad-hoc scripts:

1. `page.on("console", …)` and/or CDP `Console.enable` / `Runtime.enable`
2. `page.goto(..., wait_until="domcontentloaded")` then `page.wait_for_timeout(N)`
   (not a long `time.sleep` that ignores Playwright’s event pump)
3. Watch for `EXAMPLE_RESULT=` lines (autotest) and `PythonError` / `pageerror`
4. Give every probe a **wall-clock budget** and close the browser when it expires

## Matrix / autotest

```bash
.venv/bin/python tools/example_test_kit.py --no-unit-tests --only-runtime pyscript
.venv/bin/python tools/example_test_kit.py --no-unit-tests --only-runtime pyscript \
  --only-example calculator bouncing_balls
```

- Results: `.cursor/example_test_results.json`
- Autotest ignores the JS-only `smoke: js_timer` payload; it waits for a real
  Python `EXAMPLE_RESULT=` (or times out as `hang`)
- On WASM, `multimer.Timer` is typically **unavailable** (async-only runtime);
  embed arms a JS `setTimeout` and/or a cooperative
  [`set_deadline_hook`](../docs/concepts/multimer.md#development--troubleshooting--deadline-hooks)
  so sync loops can still finish under autotest

## Multimer on PyScript — mental model

| Fact | Implication |
|------|-------------|
| `board_config` sets `timer_async=True` for `PSDisplay` | Prefer `dual_main` / `run` / async mains for gallery demos |
| Sync `sleep_ms` → `time.sleep_ms` | Blocks JS; setTimeout / Playwright evaluate may not run until Python returns |
| `await asyncio.sleep` / async multimer sleep | **Does** yield; JS timers and Playwright stay responsive |
| `multimer.Timer` may be `None` | Sync hardware-style timers are not the WASM path; use `AsyncTimer` / asyncio |
| `set_deadline_hook` | **Harness/debug only** — not for production `load.html` demos |

When debugging timer or loop behaviour:

1. Confirm whether the example is **async entry** (import returns, loop on the
   event loop) or **sync `while True` at import time**.
2. Log with **string-only** `console.log` from Python (`from js import console`) —
   passing nested Python `dict`/`list` into `js.JSON.stringify` / `fetch` option
   objects often raises `'list' object has no attribute 'toJSON'`.
3. Do not attach arbitrary attributes to function objects on MicroPython
   (`fn._flag = …` fails); use module-level state.
4. Distinguish **Python idle after an exception** (JS timers fire, false “ok”
   smoke) from **Python stuck in a sync loop** (no JS timers, matrix `hang`).

## Instrumentation hygiene

- Prefer temporary `console.log("[pydisplay:…] …")` strings over FFI-heavy
  logging while ASYNCIFY may be active.
- Remove probe scripts and debug noise before committing unless the tool is
  meant to stay under `tools/` (the `ps_*.py` helpers are kept on purpose).
- After library changes under `src/lib/`, re-run a **small** Playwright probe
  and/or `--only-example` matrix cells before claiming a fix; a full PyScript
  matrix is slow (~10+ minutes).

## Quick checklist

1. `serve.py` up; COI headers present if SharedArrayBuffer/WASM needs them
2. Correct `modules=` / `manifests=`
3. Playwright console capture (not only screenshots)
4. Classify async vs sync entry; remember sync sleep does not yield to JS
5. Autotest: look for non-`js_timer` `EXAMPLE_RESULT=`
6. Kill wedged browsers; prefer hard timeouts
7. Keep multimer free of product-specific imports — use `set_deadline_hook` from
   harness code only
