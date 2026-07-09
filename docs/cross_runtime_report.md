# Cross-runtime example matrix report

**Last updated:** 2026-07-09 (CP rebuild + targeted matrix; 34/34 MP and CP)  
**pydisplay HEAD:** `bc20d257` + `framebuf` shim (local, may be unpushed)  
**graphics-cmod:** `a629b7d` (`Draw.circle`; may be unpushed)  
**Harness:** `tools/example_test_kit.py --all-except-harness --order runtimes --no-unit-tests --only-runtime micropython micropython.exe circuitpython cpython-venv python.exe`  
**Baseline (historical):** `9abf8d6a` — 350 cells, 222 pass / 128 fail  
**Stale full matrix (pre–cmod API batch):** Run A below — 192 pass / 158 fail (superseded for MP by targeted retest)

---

## Session objectives (2026-07-09)

1. **graphics-cmod ↔ `src/lib/graphics`:** 100% parity. Fix each gap at the cmod when found (no example-side workarounds).
2. **`timer_async`:** All examples must pass with **`timer_async=False` and `timer_async=True`**. Real async path only — no sync fallbacks when async is selected.
3. **Matrix:** Prefer **targeted** `--only-example` runs until pass rates stabilize; full 350-cell matrix only when needed.
4. **Verification:** Agent runs targeted matrix / harness locally and marks fixes done in this report. **Do not ask Brad to reproduce** unless the agent cannot run the test or is genuinely uncertain.
5. **Hygiene:** Revert failed fix attempts; do not leave dead code.

See `.cursor/rules/graphics-parity-and-timer-async.mdc` and `~/.cursor/rules/fix-not-workaround.mdc`.

---

## Fixes this session (post–`3363982` batch)

| Area | Fix | Repo |
|------|-----|------|
| `multimer.run` / `from multimer import run` on MP | `__getattr__` loads `multimer.loop` via `__import__(__name__ + ".loop", …)` — avoids MP re-entering `__getattr__('loop')` | pydisplay `multimer/__init__.py` |
| `eventsys_touch_test` with `timer_async=True` | Same multimer fix (example uses `multimer.run(main_async)`) | pydisplay |
| `pbm_create_new` `Draw.circle` | Added `Draw.circle` binding → `gfx_shapes_circle` | graphics-cmod `gfx_bindings_mp.c` |
| `bmp565_sprite_transparent` | `DisplayBuffer.blit_transparent` delegates to native `graphics.blit_transparent` | pydisplay `displaybuf.py` |
| `nano_gui_simpletest` | `ensure_nano_gui` patches `gui.core.nanogui.refresh` to accept `graphics.FrameBuffer` (cmod) in addition to builtin `framebuf` | pydisplay `ensure_nano_gui.py` |
| `framebuf_simpletest` / CP `nano_gui` | `add_ons/framebuf.py` prefers native `graphics` over missing `graphics._framebuf` on cmod | pydisplay `add_ons/framebuf.py` |

**MP rebuild:** `./build_mp.sh --port unix --variant standard` after `Draw.circle` cmod change.

---

## Targeted matrix — micropython (2026-07-09)

**Result: 34/34 ok** (SDLDisplay backend). Commits: pydisplay `bc20d257`, graphics `a629b7d`.

## Targeted matrix — circuitpython (2026-07-09)

**Command:** same 34-example cluster after `./build_target.sh cp-unix` (graphics `a629b7d`).

**Result: 34/34 ok** after `add_ons/framebuf.py` shim (pydisplay post-`bc20d257`).

Examples (both runtimes): `alien`, `apollo`, `bmp565_*` (6), `bouncing_balls`, `boxlines`, `calculator`, `chango`, `color_test`, `displaybuf_simpletest`, `eventsys_touch_test`, `feathers`, `font_*`, `fonts`, `framebuf_simpletest`, `graphics_*`, `hello`, `joystick_list_select`, `logo`, `nano_gui_simpletest`, `palettes_cube`, `pbm_create_new`, `pydisplay_demo`, `pydisplay_demo_async`, `scroll_touch_test`, `tower_climb`, `widgets_calc`, `widgets_console`, `widgets_list`.

**Inference:** Stale Run A MP/CP error counts (~45–46 each) were dominated by pre–`3363982` cmod gaps plus session fixes. Full matrix not re-run yet.

---

## Phase 0 — Rebuilds

| Target | Command | Verified |
|--------|---------|----------|
| MicroPython unix | `./build_mp.sh --port unix --variant standard` | `import graphics` → `native_cmod`; targeted 34/34 ok |
| MicroPython Windows | `./build_mp.sh --port windows --variant dev` | Not re-tested this session |
| CircuitPython unix | `./build_target.sh cp-unix` | `import graphics` → `native_cmod`; targeted **34/34 ok** |
| CPython | editable `graphics-cmod` in pydisplay `.venv` | `test_parity.py` ok (prior) |

Symlinks: `~/bin/micropython` → `build-dev`, `~/bin/circuitpython` → `build-coverage`.

---

## Run A — sync timer (`timer_async=False`, default desktop) — STALE

**Config:** historical; desktop now uses `timer_async=True` in `board_config.py` line 84.

| Metric | Count |
|--------|------:|
| Cells | 350 |
| **Pass** | **192** |
| Fail | 158 |

### Per runtime (Run A)

| Runtime | ok | error | hang | exit |
|---------|---:|------:|-----:|-----:|
| micropython | 25 | 45 | 0 | 0 |
| micropython.exe | 10 | 43 | 5 | 12 |
| circuitpython | 24 | 46 | 0 | 0 |
| cpython-venv | 64 | 0 | 5 | 1 |
| python.exe | 69 | 0 | 1 | 0 |

**Artifacts:** `.cursor/example_test_results_sync.json`

**Note:** MP column superseded for graphics cluster by **34/34 targeted retest** above.

---

## Run B — async timer (`timer_async=True`) — STALE / SUPERSEDED

Run B predates `dee5370d` (`Runtime.arm_async_refresh`, `multimer.run`). Post-fix limited smoke: cpython-venv 8/8 ok; MP failures were cmod API gaps (mostly fixed).

**Artifacts:** `.cursor/example_test_results_async.json`

---

## Remaining (next)

| # | Item | Notes |
|---|------|-------|
| 1 | **MP.exe targeted matrix** | Teardown cluster (12 exit, 5 hang in Run A); not retested |
| 2 | **cpython-venv hangs** | 5 in Run A: `displaysys_fill_rect_test`, `eventsys_touch_test`, `lv_test_timer_sync`, `palettes_material`, `scroll_touch_test` |
| 3 | **`lv_touch_test`** | exit_-11 (SIGSEGV, LVGL) |
| 4 | **`timer_async=True` targeted matrix** | Desktop `board_config` already `timer_async=True`; smoke MP async examples next |
| 5 | Full matrix ×2 | Only after targeted passes stabilize on MP.exe |
| 6 | graphics-cmod parity audit | Line-by-line vs `src/lib/graphics`; fix remaining gaps |
| 7 | Push graphics + pydisplay | When ready |
| 8 | PyScript matrix | serve.py / port 8000 |

---

## Rules of thumb

1. Loop examples: call `runtime.poll()` before checking `quit_requested`.
2. Test harness: test-mode `_handle_quit` → `stop_timer()` only; no `display.quit()` from inject thread.
3. DisplayBuffer loops: `runtime.stop_timer()` before manual poll/`show()` loop.
4. **`timer_async`:** Desktop SDL/PG use `timer_async=True`. Display refresh defers until `multimer.run()` / `dual_main` / `run_forever` starts the asyncio loop and calls `runtime.arm_async_refresh()`.
5. CPython test mode: wrapper `os._exit`; oneshot examples skip `display_drv.quit()`.
6. MP matrix from `src/`: `lib/` before `.frozen` (path.py prepend).
7. **Targeted matrix:** `--only-example <name> … --only-runtime micropython` before full grid.
8. **Who verifies:** Agent owns verification (targeted matrix, rebuilds, harness). Update this report after each major fix. Manual runs from Brad only when blocked (missing runtime, hardware, or ambiguous result).

---

## Re-run commands

**Targeted (preferred):**

```bash
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy .venv/bin/python tools/example_test_kit.py \
  --no-unit-tests --only-runtime micropython \
  --only-example calculator widgets_calc bmp565_blit eventsys_touch_test
```

**Full matrix:**

```bash
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy .venv/bin/python tools/example_test_kit.py \
  --all-except-harness --order runtimes --no-unit-tests \
  --only-runtime micropython micropython.exe circuitpython cpython-venv python.exe
```

Results: `.cursor/example_test_results.json` (copy to `_sync.json` / `_async.json` when comparing configs).
