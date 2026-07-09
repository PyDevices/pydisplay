# Cross-runtime example matrix report

**Last updated:** 2026-07-09 (full matrix ×2 after MP/CP rebuild)  
**pydisplay HEAD:** `ad373bde`  
**Harness:** `tools/example_test_kit.py --all-except-harness --order runtimes --no-unit-tests --only-runtime micropython micropython.exe circuitpython cpython-venv python.exe`  
**Baseline (historical):** `9abf8d6a` — 350 cells, 222 pass / 128 fail  
**Prior stale matrix:** 350 cells, 282 pass / 68 fail (pre-rebuild, mixed graphics stack)

---

## Phase 0 — Rebuilds (2026-07-09)

| Target | Command | Verified |
|--------|---------|----------|
| MicroPython unix | `./build_mp.sh --port unix --variant standard` | `import graphics` → `native_cmod` |
| MicroPython Windows | `./build_mp.sh --port windows --variant dev` | `micropython.exe` → `native_cmod` |
| CircuitPython unix | `apply_cp_unix_graphics_patches.sh` + `build_cp.sh --port unix --variant coverage` | `import graphics` → `native_cmod` |
| CPython | editable `graphics-cmod` @ `036e9b4` in pydisplay `.venv` | `test_parity.py` ok |

Symlinks: `~/bin/micropython`, `~/bin/micropython.exe` → `build-dev`, `~/bin/circuitpython` → `build-coverage`.

**TestPyPI:** `graphics-cmod` **v0.0.3** published (`6166038` — CPython wheel GCC 14 fix only; no MP/CP rebuild needed).

**Note:** First matrix attempt included pyscript/jupyter; PyScript server failed to start on port 8000. Both reported runs use **5 subprocess runtimes only** (matches historical desktop matrix scope).

---

## Run A — sync timer (`timer_async=False`, default desktop)

**Config:** `board_config.py` line 84 unchanged (`Runtime(..., host_read=get_events)`).

| Metric | Count |
|--------|------:|
| Cells | 350 |
| **Pass** | **192** |
| Fail | 158 |
| — error | 134 |
| — hang | 11 |
| — exit | 13 |

### Per runtime (Run A)

| Runtime | ok | error | hang | exit |
|---------|---:|------:|-----:|-----:|
| micropython | 25 | 45 | 0 | 0 |
| micropython.exe | 10 | 43 | 5 | 12 |
| circuitpython | 24 | 46 | 0 | 0 |
| cpython-venv | 64 | 0 | 5 | 1 |
| python.exe | 69 | 0 | 1 | 0 |

**Artifacts:** `.cursor/example_test_results_sync.json`

### Run A — notable outcomes

**cpython-venv / python.exe:** Strong pass rate (64/70, 69/70). Remaining cpython-venv issues: hangs on `displaysys_fill_rect_test`, `eventsys_touch_test`, `palettes_material`, `scroll_touch_test`; `lv_touch_test` exit_-11 (SIGSEGV).

**micropython / circuitpython (native cmod):** Many errors — examples expect Python `graphics` API (`FrameBuffer` duck typing, `BMP565` subscript/bpp, `from_file`, keyword args, `text16`, etc.). Confirms cmod is active; example/cmod API gaps dominate (not display-driver regressions).

**micropython.exe:** Teardown cluster persists — 12 exit, 5 hang (e.g. `displaybuf_simpletest` exit_3, `displaysys_block_test` exit_5, encoder/touch hangs). 10 ok vs 25 on MP unix.

**Fixed vs prior incremental smoke:** `displaybuf_blit`, `scroll_touch_test_displaybuf` **ok** on cpython-venv and micropython in full matrix.

---

## Run B — async timer (`timer_async=True` on desktop SDL/PG branch)

**Config:** line 84 temporarily `Runtime(..., host_read=get_events, timer_async=True)` (reverted after run).

| Metric | Count | Δ vs Run A |
|--------|------:|-----------:|
| Cells | 350 | — |
| **Pass** | **59** | **−133** |
| Fail | 291 | +133 |
| — error | 285 | +151 |
| — hang | 5 | −6 |
| — exit | 1 | −12 |

### Per runtime (Run B)

| Runtime | ok | error | hang | exit |
|---------|---:|------:|-----:|-----:|
| micropython | 27 | 43 | 0 | 0 |
| micropython.exe | 2 | 67 | 0 | 1 |
| circuitpython | 24 | 46 | 0 | 0 |
| cpython-venv | 3 | 67 | 0 | 0 |
| python.exe | 3 | 62 | 5 | 0 |

**Artifacts:** `.cursor/example_test_results_async.json`

### Run B — analysis (superseded)

Run B predates the **timer_async host** fix (`Runtime.arm_async_refresh`, `multimer.run`, deferred refresh). That run failed because refresh armed `AsyncTimer` at import without a loop.

**Post-fix limited matrix** (`timer_async=True` on desktop): cpython-venv **8/8** ok on smoke set; MP failures are graphics cmod API gaps only.

---

## Remaining (next)

| # | Item | Notes |
|---|------|-------|
| 1 | MP/CP example vs cmod API | ~45–46 errors/runtime: `FrameBuffer required`, BMP565, `from_file`, kwargs, `text16` |
| 2 | MP.exe teardown | 12 exit + 5 hang in Run A; async made worse (67 errors) |
| 3 | cpython-venv hangs | 5 in Run A: fill_rect, touch, palettes_material, scroll_touch |
| 4 | `lv_touch_test` | exit_-11 on cpython-venv (LVGL; `matrix=false` in manifest?) |
| 5 | graphics-cmod TestPyPI v0.0.3 | **published** (`6166038`) |
| 6 | Full matrix + pyscript | Optional; fix serve.py / port 8000 for launcher runtimes |

---

## Rules of thumb

1. Loop examples: call `runtime.poll()` before checking `quit_requested`.
2. Test harness: test-mode `_handle_quit` → `stop_timer()` only; no `display.quit()` from inject thread.
3. DisplayBuffer loops: `runtime.stop_timer()` before manual poll/`show()` loop.
4. **`timer_async`:** Desktop SDL/PG use `timer_async=True` like PyScript/Jupyter. Display refresh defers until `multimer.run()` / `dual_main` / `run_forever` starts the asyncio loop and calls `runtime.arm_async_refresh()`. Loop examples should use `run_forever` or `dual_main`, not raw `while` + `sleep_ms`.
5. CPython test mode: wrapper `os._exit`; oneshot examples skip `display_drv.quit()`.
6. MP matrix from `src/`: `lib/` before `.frozen` (path.py prepend).

---

## Re-run command

```bash
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy .venv/bin/python tools/example_test_kit.py \
  --all-except-harness --order runtimes --no-unit-tests \
  --only-runtime micropython micropython.exe circuitpython cpython-venv python.exe
```

Results: `.cursor/example_test_results.json` (copy to `_sync.json` / `_async.json` when comparing configs).
