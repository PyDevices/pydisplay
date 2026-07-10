# Cross-runtime example matrix report

**Last updated:** 2026-07-09 (framebuf refactor complete; MP.exe rebuild + manifest fix)  
**pydisplay HEAD:** local (uncommitted — framebuf refactor + report)  
**graphics-cmod:** `a629b7d`+ (windows rebuild links current cmod)  
**cmods:** `manifest.py` includes `windows/variants/dev` for asyncio freeze (uncommitted in cmods repo)  
**Harness:** `tools/example_test_kit.py`  
**Baseline (historical):** `9abf8d6a` — 350 cells, 222 pass / 128 fail  
**Stale full matrix:** Run A below — 192 pass / 158 fail (superseded for MP unix/CP by 34/34 targeted)

---

## Session objectives

1. **graphics-cmod ↔ `src/lib/graphics`:** 100% parity. Fix at cmod, not example workarounds.
2. **`timer_async`:** All examples pass with **`timer_async=False` and `timer_async=True`**.
3. **Matrix:** Prefer targeted `--only-example` runs; full 350-cell only when needed.
4. **Verification:** Agent runs matrix locally; update this report. Do not ask Brad to reproduce unless blocked.
5. **framebuf refactor:** **DONE** — see `.cursor/framebuf-graphics-refactor-plan.md` (Post-build dedupe still open).

---

## Targeted matrix — micropython unix post-framebuf (2026-07-09)

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

1. **Stale `micropython.exe`** — linked graphics cmod missing `from_file`, `text16`, full `mp_canvas_resolve` → `FrameBuffer required` / `canvas required` / BMP565 API errors.
2. **Missing frozen asyncio** — `cmods/manifest.py` fallback chain never included `ports/windows/variants/dev/manifest.py`, so `uasyncio`/`asyncio` absent on MP.exe.

### Fixes applied

| Fix | Repo |
|-----|------|
| `./build_mp.sh --port windows --variant dev` | cmods (relinks current graphics cmod) |
| Include `$(PORT_DIR)/variants/dev/manifest.py` in root frozen manifest | `cmods/manifest.py` |

### Still failing on MP.exe (19/36 ok)

| Bucket | Examples | Notes |
|--------|----------|-------|
| **hang** (5) | `apollo`, `color_test`, `feathers`, `font_simpletest2`, `scroll_touch_test` | Harness timeout @ 5s; no `EXAMPLE_RESULT` (e.g. `apollo` empty stdout) |
| **exit_5** (11) | `bmp565_sprite_transparent`, `bouncing_balls`, `boxlines`, `font_simpletest`, `font_simpletest3`, `hello`, `joystick_list_select`, `tower_climb`, `widgets_calc`, `widgets_console`, `widgets_list` | Ran ~5s, `returncode=5`, no result JSON — loop/quit contract or wine/SDL edge |

**Next for MP.exe:** bucket exit_5 vs hang; compare same examples on `micropython` unix; check quit injection / `EXAMPLE_RESULT` contract on windows port.

---

## cpython-venv — hang bucket (2026-07-09)

**Stale (Run A).** Re-tested the five names from Run A:

| Example | Result |
|---------|--------|
| `displaysys_fill_rect_test` | ok |
| `eventsys_touch_test` | ok |
| `palettes_material` | ok |
| `scroll_touch_test` | ok |
| `lv_test_timer_sync` | `matrix=false` (excluded) |

MP unix async smoke (`pydisplay_demo_async`, `eventsys_touch_test`, `alien`, `calculator`): **4/4 ok**.

`lv_touch_test` on cpython-venv: `RuntimeError: no running event loop` (`matrix=false`).

---

## Phase 0 — Rebuilds

| Target | Command | Verified |
|--------|---------|----------|
| MicroPython unix | `./build_mp.sh --port unix --variant standard` | 34/34 targeted ok |
| **MicroPython Windows** | `./build_mp.sh --port windows --variant dev` | **Rebuilt 2026-07-09**; 19/36 cluster ok |
| CircuitPython unix | `./build_target.sh cp-unix` | 34/34 + post-refactor 2/2 ok |
| CPython | editable `graphics-cmod` in `.venv` | parity tests ok |

Symlinks: `~/bin/micropython` → unix build; `~/bin/micropython.exe` → `ports/windows/build-dev/micropython.exe`.

---

## Run A — sync timer — STALE

350 cells, 192 pass / 158 fail. MP/CP columns superseded by 34/34 targeted retests. MP.exe column superseded by 19/36 post-rebuild cluster.

**Artifacts:** `.cursor/example_test_results_sync.json`

---

## Remaining (next)

| # | Item | Status |
|---|------|--------|
| 1 | **MP.exe exit_5 + hang buckets** | 11 + 5 in 36-cluster; investigate vs unix |
| 2 | ~~cpython-venv hangs~~ | **Cleared** (stale) |
| 3 | **`lv_touch_test`** | cpython event loop; `matrix=false` |
| 4 | ~~framebuf refactor verify~~ | **DONE** — CP 2/2; MP manifest 67/67 |
| 5 | Full matrix ×2 | Defer until MP.exe + framebuf stable |
| 6 | graphics-cmod parity audit | Ongoing |
| 7 | Push cmods + pydisplay | When Brad asks |
| 8 | PyScript matrix | Not run |
| 9 | **framebuf single-source dedupe** | Post-build (Brad); see refactor plan |

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

**Rebuild MP.exe after cmod/manifest changes:**

```bash
cd ~/github/cmods && ./build_mp.sh --port windows --variant dev
```

Results: `.cursor/example_test_results.json`
