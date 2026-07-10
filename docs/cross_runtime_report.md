# Cross-runtime example matrix report

**Last updated:** 2026-07-10  
**Harness:** `tools/example_test_kit.py` · **Manifest:** `tools/example_test_manifest.toml`  
**Docs:** [`docs/testing/example-runtimes.md`](testing/example-runtimes.md)

---

## Current status

| Area | Result |
|------|--------|
| **graphics / framebuf parity** | `compare_graphics_mp.py` + `compare_framebuf_mp.py` pass on MP unix |
| **micropython unix** | 67/67 ok (full manifest, SDL dummy) |
| **circuitpython** | 34/34 ok |
| **micropython.exe** | **36/36 ok** graphics cluster; harness fixes for poll-deadline quit (`3d226ce5`) |
| **Full desktop matrix** | **320/335** (`timer_async=0`) · **325/335** (`timer_async=1`) — re-run after `3d226ce5` for updated MP.exe rows |

Desktop timers: default **`timer_async=False`**; set **`PYDISPLAY_TIMER_ASYNC=1`** for asyncio mode. `Runtime: timer_async=…` prints at init.

---

## pdwidgets rework (2026-07-10)

The 11 `widgets_*.py` examples are now first-class matrix members (`matrix = false`
removed) and 10 of them (all but the `widgets_stub` boilerplate) are in the
PyScript browser gallery (`# pyscript skip: gallery` removed, gallery regenerated).

| Runtime | `timer_async=0` | `timer_async=1` |
|---------|-----------------|-----------------|
| `cpython-venv` | **11/11 ok** | **11/11 ok** |
| `micropython` (unix) | **11/11 ok** | **11/11 ok** |
| `circuitpython` (unix) | **11/11 ok** | pre-existing CP-unix asyncio limit¹ |
| `jupyter` (JNDisplay, asyncio-native) | — | **11/11 ok** (real render) |
| `pyscript` (PSDisplay, asyncio-native) | — | loads/runs² |

**Timer rework:** pdwidgets now owns **no** timer — frames are driven from one
poll function via `multimer.loop.run_forever` (sync `while` loop or shared
asyncio loop, chosen from `runtime.timer_async`). `Display.timer` is always
`None` in both modes, so a sync `Timer` never races the asyncio loop
(the former "competing timer" bug). Verified:
`PYDISPLAY_TIMER_ASYNC=1 … python -c "import board_config, pdwidgets as pd; pd.init_timer(10); assert pd.Display.timer is None"`.

¹ **CircuitPython unix + `PYDISPLAY_TIMER_ASYNC=1`** raises
`AttributeError: 'SingletonGenerator' object has no attribute '__await__'` for
**every** async example (core `pydisplay_demo_async` fails identically) — a
pre-existing CP-unix/`multimer` asyncio limitation, not pdwidgets. The default
matrix runs `timer_async=0`, where CP passes 11/11.

² **PyScript** (`micropython-webassembly-pyscript@1.28.0-6`): the pinned CDN
firmware ships **no frozen `asyncio`/`_asyncio`**, so `multimer.loop.run` falls
through to `multimer._mpasyncio` (needs the `_asyncio` builtin) and raises
`AttributeError: module 'multimer' has no attribute '_mpasyncio'` at loop
launch. This hits **the entire gallery** — `calculator`, `paint`,
`eventsys_simpletest`, `pydisplay_demo_async` all fail identically — so it is a
firmware/`multimer` limitation (both out of scope here), not pdwidgets. The kit
still reports `PSDisplay, ok` because the `js_timer` autotest smoke fires after
the display backend initializes. Two in-scope packaging fixes were needed just
to reach that point (both in `scripts/install_gen_manifests.py`): the generated
`pyscript.toml`/`packages/*.json` were stale after the `framebuf` refactor
(referenced removed `_framebuf.py`/`_capabilities.py` → 404, blank canvas) and
never listed `env_util.py` (imported by `board_config`).

---

## Full desktop matrix (2026-07-10)

**Command:** parallel passes, `PYDISPLAY_TIMER_ASYNC=0` and `1`, 5 runtimes (`micropython`, `micropython.exe`, `circuitpython`, `cpython-venv`, `python.exe`), `--order examples`, SDL dummy.

| Mode | Pass | Notes |
|------|-----:|-------|
| `timer_async=0` | **320/335** | 15 `matrix=false` rows listed but not executed |
| `timer_async=1` | **325/335** | async mode slightly better on MP.exe widgets |

**Artifacts:** `.cursor/example_test_results_timer_async_{0,1}.json`

**Known failures (both modes unless noted):**

| Issue | Examples / runtimes |
|-------|---------------------|
| `FrameBuffer` has no `circle` | ✅ resolved — `graphics-cmod` ships `circle`/`round_rect`; widgets `11/11 ok` on MP/CP (see pdwidgets section) |
| `lv_touch_test` | skipped on `micropython.exe` (`skip_runtimes`); `matrix=false` / event-loop work on `cpython-venv` |
| `timer_simpletest` | was `TypeError` @ `circuitpython` (`timer_async=1` only); spot retest passes |

**Fixed @ `micropython.exe` (`3d226ce5`):** `displaysys_simpletest`, `eventsys_encoder_test`, `console_advanced_demo` — examples honor `runtime.quit_requested`; `display_driver.run` exits on quit; `lv_utils` optional `asyncio` import.

---

## MP.exe graphics cluster (36 examples)

`SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy`, `micropython.exe` only.

| Stage | ok | hang | exit |
|-------|---:|-----:|-----:|
| Stale build | 3 | — | 32 error |
| Post-rebuild | 19 | 5 | 11 exit_5 |
| Post-harness (`8742556b`) | 30 | 2 | 4 |
| **Final (`89f098c2`)** | **36** | **0** | **0** |
| **Harness quit (`3d226ce5`)** | displaysys / encoder / console ok on MP.exe full kit |

**Fixes (no multimer backend edits):**

- Harness: `Runtime.poll` deadline quit on hosts without `threading`; test mode skips auto-refresh timer.
- Examples: poll-driven scroll/tick when `timer_async=False`; check `runtime.quit_requested` (not only `QUIT` events).
- `eventsys_touch_test`: exit on `quit_requested` (interactive calibration; does not complete in headless runs).

---

## cpython-venv notes

- `lv_touch_test`: `RuntimeError: no running event loop` (`matrix=false`).
- Prior “hang bucket” from old full matrix: stale; spot retests pass.

---

## Parity tools (MP unix)

```bash
micropython tools/compare_framebuf_mp.py
micropython tools/compare_graphics_mp.py
```

Visual text compare: `src/examples/framebuf_text_compare.py`.

---

## Rebuilds

| Target | Command |
|--------|---------|
| MP unix | `cd ~/github/cmods && ./build_mp.sh --port unix` |
| MP Windows | `./build_mp.sh --port windows --variant dev` |
| CircuitPython unix | `./build_target.sh cp-unix` |
| Font sync | `cd ~/github/cmods/graphics && python3 scripts/sync_fonts.py --pydisplay ~/github/pydisplay` |

Symlinks: `~/bin/micropython`, `~/bin/micropython.exe`.

---

## Matrix commands

**Desktop matrix (parallel, 5 runtimes, example order):**

```bash
tools/run_full_matrix_both_timer_modes.sh
```

**Single pass:**

```bash
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy PYDISPLAY_TIMER_ASYNC=0 \
  .venv/bin/python tools/example_test_kit.py --no-unit-tests --order examples \
  --only-runtime micropython micropython.exe circuitpython cpython-venv python.exe \
  --results-json .cursor/example_test_results_timer_async_0.json
```

**MP.exe 36-cluster** (quick regression):

```bash
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy .venv/bin/python tools/example_test_kit.py \
  --no-unit-tests --only-runtime micropython.exe \
  --only-example alien apollo bmp565_blit bmp565_scroll bmp565_scroll_sprite bmp565_sprite \
  bmp565_sprite_transparent bouncing_balls boxlines calculator chango color_test \
  displaybuf_simpletest eventsys_touch_test feathers font_simpletest font_simpletest2 \
  font_simpletest3 fonts framebuf_simpletest graphics_simpletest graphics_area_test hello \
  joystick_list_select logo nano_gui_simpletest palettes_cube pbm_create_new pydisplay_demo \
  pydisplay_demo_async scroll_touch_test tower_climb widgets_calc widgets_console widgets_list
```

**Results:** `.cursor/example_test_results.json` (latest run); timer-mode copies:  
`.cursor/example_test_results_timer_async_0.json`, `.cursor/example_test_results_timer_async_1.json`.

---

## Remaining

| Item | Status |
|------|--------|
| Full desktop matrix sync + async | **Done** — 320–325/335 per mode; see above |
| `lv_touch_test` on cpython | `matrix=false`; needs event-loop work |
| PyScript matrix | Loads via Playwright + serve; async loop launch blocked by CDN firmware without frozen `asyncio` (whole gallery, see pdwidgets §²) |
| Push cmods + graphics | When requested |
