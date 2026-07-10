# Cross-runtime example matrix report

**Last updated:** 2026-07-09 (graphics cmod font parity; compare tools)  
**pydisplay HEAD:** ahead of `origin/main` (compare tools + font docs; see git log)  
**graphics-cmod:** romfont headers + `gfx_shapes_line` parity + `scripts/sync_fonts.py` (rebuild MP unix after pull)  
**cmods:** `manifest.py` asyncio freeze on windows dev (`3984ee8`+); MP unix links graphics from submodule  
**Harness:** `tools/example_test_kit.py`  
**Baseline (historical):** `9abf8d6a` — 350 cells, 222 pass / 128 fail  
**Stale full matrix:** Run A below — 192 pass / 158 fail (superseded for MP unix/CP by targeted retests)

---

## Session objectives

1. **graphics-cmod ↔ `src/lib/graphics`:** **DONE** — `tools/compare_graphics_mp.py` all checks pass on MP unix after romfont header regen.
2. **`timer_async`:** All examples pass with **`timer_async=False` and `timer_async=True`** (MP unix manifest).
3. **Matrix:** Prefer targeted `--only-example` runs; full 350-cell deferred until MP.exe stable.
4. **Verification:** Agent runs matrix locally; update this report.
5. **framebuf refactor + dedupe:** **DONE** — `tools/sync_framebuf.py`, `tools/compare_framebuf_mp.py`.

---

## Parity tools (MP unix)

| Tool | Compares |
|------|----------|
| `tools/compare_framebuf_mp.py` | C `framebuf` vs `add_ons/framebuf.py` |
| `tools/compare_graphics_mp.py` | `graphics` cmod vs staged `src/lib/graphics` |

```bash
micropython tools/compare_framebuf_mp.py
micropython tools/compare_graphics_mp.py
```

Visual 2×2 text compare: `src/examples/framebuf_text_compare.py` (framebuf + graphics quadrants).

**graphics cmod fixes (2026-07-09):** Regenerated `font_8x8/14/16.h` from pydisplay romfont (`scripts/sync_fonts.py`); dropped corrupt headers + unused `font_petme128_8x8.h`; aligned `gfx_shapes_line` with Python `_shapes.line`.

---

## Targeted matrix — micropython unix (2026-07-09)

**Result: 67/67 ok** (full example manifest, SDLDisplay) after framebuf refactor.

---

## Targeted matrix — circuitpython (2026-07-09)

**Result: 34/34 ok** (prior cluster). Post-refactor spot check: `framebuf_simpletest`, `nano_gui_simpletest` **2/2 ok**.

---

## Targeted matrix — micropython.exe (2026-07-09, post-rebuild)

**Command:** 36-example graphics cluster, `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy`.

| Metric | Before rebuild | After rebuild + asyncio manifest |
|--------|----------------:|---------------------------------:|
| **ok** | 3 | **19** |
| hang | — | 5 |
| exit_5 | — | 11 |
| error | 32 | 0 |

### Root cause (confirmed)

1. **Stale `micropython.exe`** — linked graphics cmod missing APIs → rebuild `build_mp.sh --port windows --variant dev`.
2. **Missing frozen asyncio** — `cmods/manifest.py` now includes `ports/windows/variants/dev/manifest.py`.

### Still failing on MP.exe (19/36 ok)

| Bucket | Examples | Notes |
|--------|----------|-------|
| **hang** (5) | `apollo`, `color_test`, `feathers`, `font_simpletest2`, `scroll_touch_test` | Harness timeout @ 5s; no `EXAMPLE_RESULT` |
| **exit_5** (11) | `bmp565_sprite_transparent`, `bouncing_balls`, `boxlines`, `font_simpletest`, `font_simpletest3`, `hello`, `joystick_list_select`, `tower_climb`, `widgets_calc`, `widgets_console`, `widgets_list` | `returncode=5`, no result JSON — loop/quit contract |

**Next for MP.exe:** bucket exit_5 vs hang; compare same examples on `micropython` unix; quit / `EXAMPLE_RESULT` on windows port.

---

## cpython-venv

**Hang bucket (Run A): stale.** Re-tested five names: **4/4 ok** (`lv_test_timer_sync` excluded).

`lv_touch_test`: `RuntimeError: no running event loop` (`matrix=false`).

MP unix async smoke: **4/4 ok**.

---

## Phase 0 — Rebuilds

| Target | Command | Verified |
|--------|---------|----------|
| MicroPython unix | `./build_mp.sh --port unix` | 67/67 manifest; compare tools pass |
| MicroPython Windows | `./build_mp.sh --port windows --variant dev` | 19/36 cluster (rebuild after graphics font fix TBD on .exe) |
| CircuitPython unix | `./build_target.sh cp-unix` | 34/34 + 2/2 spot |
| CPython | editable `graphics-cmod` in `.venv` | unit tests ok |

Symlinks: `~/bin/micropython` → unix build; `~/bin/micropython.exe` → windows dev build.

---

## Run A — sync timer — STALE

350 cells, 192 pass / 158 fail. Superseded by targeted retests above.

**Artifacts:** `.cursor/example_test_results_sync.json`

---

## Remaining (next)

| # | Item | Status |
|---|------|--------|
| 1 | **MP.exe exit_5 + hang** | 11 + 5 in 36-cluster — **primary matrix work** |
| 2 | ~~cpython-venv hangs~~ | Cleared (stale) |
| 3 | **`lv_touch_test`** | cpython event loop; `matrix=false` |
| 4 | ~~framebuf / graphics parity~~ | **DONE** — compare tools green |
| 5 | Full 350-cell matrix | Defer until MP.exe stable |
| 6 | PyScript matrix | Not run |
| 7 | Push cmods + pydisplay + graphics | When Brad asks |
| 8 | Rebuild **MP.exe** after graphics font commit | Recommended before re-cluster |

---

## Re-run commands

**MP.exe 36-cluster:**

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

**Parity + rebuild:**

```bash
cd ~/github/cmods/graphics && python3 scripts/sync_fonts.py --pydisplay ~/github/pydisplay
cd ~/github/cmods && ./build_mp.sh --port unix
micropython tools/compare_graphics_mp.py
```

Results: `.cursor/example_test_results.json`
