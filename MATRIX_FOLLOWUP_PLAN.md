# Matrix Follow-up Plan

**Source:** [`.cursor/example_matrix_run.log`](.cursor/example_matrix_run.log) and [`.cursor/example_test_results.json`](.cursor/example_test_results.json)  
**Branch:** `examples-post-refactor`  
**Matrix command:** `python tools/example_test_kit.py --no-unit-tests --order runtimes`

---

## Results summary

| Runtime | Pass (excl. `matrix=false`) | Notes |
|---------|----------------------------|-------|
| **micropython** | **60/60** | Reference runtime |
| **circuitpython** | **60/60** | `pbm_simpletest` needs `oneshot_timeout_s = 60` |
| **cpython-venv** | **58/58** | Skips `console_advanced_demo`, `nano_gui_simpletest` |
| **python.exe** | **58/58** | Skips `chango`, `png_test` |
| **micropython.exe** | **49/60** → improving | Harness fixes below; async examples need `dual_main()` |
| **pyscript** | **0/52** | Chromium launch blocked — missing `libnspr4.so` (WSL); see §5 |
| **jupyter** | **22/58** | Harness + JNDisplay gaps |

---

## §4 micropython.exe — debug results and fixes

### `lv_touch_test` — **FIXED** (test apparatus)

**Root cause:** `micropython.exe` has no `threading` or `_thread`. The wrapper fell back to **synchronous** quit injection *before* the example ran, calling `lv.task_handler()` via `pump_lvgl()` while LVGL was still uninitialized → `SystemExit(5)`.

**Fix applied (no example/lib changes):**

- [`tools/example_test_wrapper.py`](tools/example_test_wrapper.py): `_start_multimer_quit_schedule()` — `multimer.Timer` one-shots inject touch/quit while `display_driver.run()` pumps on the main thread.
- [`tools/quit_inject.py`](tools/quit_inject.py): `pump_lvgl()` guards with `lv.is_initialized()`.

**Verified:** `lv_touch_test` → **SDLDisplay, ok** on `micropython.exe` (~8s).

**Optional hardening (needs permission — example or add_ons):** `lv_touch_test.py` line 66 skips the cooperative duration loop on `win32`; if multimer scheduling ever fails, the example could hang until harness timeout.

### `bmp565_scroll_sprite` — **FIXED** (manifest timeout)

**Root cause:** Not a true hang — example is **very slow** on `micropython.exe` (~55s to cooperative quit). Kit timeout is `timeout_s + 5` = **35s** (default 30s), so subprocess is killed before `EXAMPLE_RESULT` prints. Linux `micropython` finishes in ~5s.

**Fix applied (test apparatus only):**

```toml
# tools/example_test_manifest.toml
[examples.bmp565_scroll_sprite]
timeout_s = 70
```

Side effect: `schedule queue full` timer noise on slow ports is benign; test still passes.

**Verified:** `bmp565_scroll_sprite` → **SDLDisplay, ok** on `micropython.exe` (~56s).

### Async examples — **`dual_main()` rewrite** (needs permission — examples)

| Example | Failure |
|---------|---------|
| `apollo`, `calculator`, `eventsys_simpletest`, `paint` | `no module named 'uasyncio'` |
| `pydisplay_demo_async` | multimer async requires asyncio |

See [app-starter dual pattern](docs/examples/app-starter.md). Remove forced `board_config.TIMER_ASYNC = True` at module top; use `dual_main(main_sync, main_async, async_mode=TIMER_ASYNC)`.

### Other micropython.exe edge cases

| Example | Approach |
|---------|----------|
| `bmp565_sprite`, `bmp565_sprite_transparent`, `testris` | `random.choice` shim (example or small lib helper — needs permission) |
| `console_advanced_demo` | Skipped on cpython-venv/python.exe/jupyter; `interactive_requires_thread` on mp.exe |

---

## §5 PyScript — re-run results (2026-06-29)

**Command:** `.venv/bin/python tools/example_test_kit.py --no-unit-tests --only-runtime pyscript`

Playwright is installed in repo **`.venv`** (not system `python`). Kit auto-starts `tools/serve.py` on port 8000 when needed.

### Result counts (52 runnable; 2 manifest skips)

| Outcome | Count |
|---------|------:|
| **ok** | 0 |
| **needs_playwright** | 0 (with `.venv/bin/python`) |
| **error** (BrowserType.launch) | **52** |
| **timeout / hang** | 0 |
| **matrix=false** (not runnable) | 2 — `hello`, `keypins_simpletest` |

**Pass rate: 0/52 (0%).** No example-level failures yet — Chromium never launched.

### Root cause — OS browser deps (not pydisplay)

Every runnable case failed the same way:

```
chrome-headless-shell: error while loading shared libraries: libnspr4.so: cannot open shared object file
```

- `pip install playwright` + `playwright install chromium` are present in `.venv`.
- WSL is missing NSS/NSPR system libraries Chromium needs.
- `sudo .venv/bin/playwright install-deps chromium` failed here (sudo password required).

### Harness notes (applied)

- [`tools/example_test_kit.py`](tools/example_test_kit.py): `_server_ready()` now treats `OSError` / `ConnectionError` (e.g. stale listener on port 8000) as not-ready instead of crashing with `RemoteDisconnected`.
- Kill a broken server before re-run: `fuser -k 8000/tcp`.

### Real failures (examples)

None — all 52 errors are infrastructure (`BrowserType.launch`), not `EXAMPLE_RESULT` failures.

### Next steps

1. **Install OS deps** (one-time, needs sudo on WSL):
   ```bash
   sudo .venv/bin/playwright install-deps chromium
   # or: sudo apt install libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libasound2
   ```
2. **Re-run column:**
   ```bash
   .venv/bin/python tools/example_test_kit.py --no-unit-tests --only-runtime pyscript
   ```
3. After Chromium launches, triage any true example failures (async demos, LVGL, missing PyScript shims) from `EXAMPLE_RESULT` / page errors.

---

## Other priorities

### P0 — Ship core refactor PR

Core four subprocess runtimes green. Commit `pbm_simpletest` `oneshot_timeout_s = 60`.

### P1 — Jupyter harness (test apparatus)

1. Add `pydisplay_test_mode` cell to `_write_jupyter_notebook()` in [`example_test_kit.py`](tools/example_test_kit.py).
2. ~~Add `skip_runtimes = ["jupyter"]` to `console_advanced_demo` (matches cpython-venv/python.exe).~~ **Done**
3. Re-run jupyter column.

### P2 — JNDisplay blit bounds (needs permission — `src/lib/displaysys/jndisplay.py`)

Clip `blit_rect` like SDL, or fix example layouts for 320px width.

### P4 — PyScript (blocked on OS deps)

Playwright + Chromium binaries are in `.venv`; **52/52 launch errors** until `libnspr4` et al. are installed. See §5.

---

## Verification

```bash
python tools/example_test_kit.py --no-unit-tests --only-example lv_touch_test --only-runtime micropython.exe
python tools/example_test_kit.py --no-unit-tests --only-example bmp565_scroll_sprite --only-runtime micropython.exe  # after timeout_s=70
.venv/bin/python tools/example_test_kit.py --no-unit-tests --only-runtime pyscript
python tools/example_test_kit.py --no-unit-tests --only-runtime jupyter
```

Results: `.cursor/example_test_results.json`

---

## Session status (2026-06-29)

| Item | Status |
|------|--------|
| `lv_touch_test` mp.exe harness | **Done** |
| `bmp565_scroll_sprite` timeout_s=70 | **Done** (~56s mp.exe) |
| `dual_main()` async examples | **Pending** (needs permission) |
| Jupyter harness + console skip | **Partial** — console `jupyter` skip done; harness cell pending |
| PyScript re-run | **Blocked** — `libnspr4.so` missing; 0/52 until `playwright install-deps` |
| `MATRIX_FOLLOWUP_PLAN.md` | **This file** |
