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
| **micropython.exe** | **36/36 ok** on graphics cluster (`timer_async=False`) |
| **Full 350-cell matrix** | In progress — sync vs async timer runs below |

Desktop timers: default **`timer_async=False`**; set **`PYDISPLAY_TIMER_ASYNC=1`** for asyncio mode. `Runtime: timer_async=…` prints at init.

---

## MP.exe graphics cluster (36 examples)

`SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy`, `micropython.exe` only.

| Stage | ok | hang | exit |
|-------|---:|-----:|-----:|
| Stale build | 3 | — | 32 error |
| Post-rebuild | 19 | 5 | 11 exit_5 |
| Post-harness (`8742556b`) | 30 | 2 | 4 |
| **Final (`89f098c2`)** | **36** | **0** | **0** |

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

**Default matrix** (67 examples × available runtimes; excludes `matrix=false` and harnesses):

```bash
# Sync timers (desktop default)
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy PYDISPLAY_TIMER_ASYNC=0 \
  .venv/bin/python tools/example_test_kit.py --no-unit-tests --order runtimes

# Async timers
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy PYDISPLAY_TIMER_ASYNC=1 \
  .venv/bin/python tools/example_test_kit.py --no-unit-tests --order runtimes
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
| Full matrix sync + async | Running / update this doc |
| `lv_touch_test` on cpython | `matrix=false`; needs event-loop work |
| PyScript matrix | Optional; needs Playwright + serve |
| Push cmods + graphics | When requested |
