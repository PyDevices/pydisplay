# Cross-runtime example matrix report

**Last updated:** 2026-07-09 (`cb6ac634`)  
**Baseline:** `9abf8d6a` — 350 cells, 222 pass / 128 fail  
**Latest full matrix:** 350 cells, **282 pass / 68 fail** (44 exit, 15 hang, 9 error) — **stale** (predates commits through `cb6ac634`; re-run needed)  
**Harness:** `tools/example_test_kit.py --all-except-harness --order runtimes` (5 runtimes, no pyscript)

---

## Commits since last full matrix

| Commit | Summary |
|--------|---------|
| `8ff1330d` | Harness quit handling + hang cluster (poll before quit, test-mode `_handle_quit`, wrapper `os._exit`, PBM composition, manifest timeouts) |
| `4ca8e1b7` | Fix `scroll_touch_test_displaybuf` hang — `runtime.stop_timer()` before poll loop; no `display.quit()` from inject thread |
| `c695451f` | SDL/PG batch compositing until `show()`; pixel_sim panel blit; proxy `blit_rect` on `DisplayBuffer` |
| `cb6ac634` | NOTES only (no example changes) |

---

## Incremental kit verify (post-fix)

Spot checks after the commits above (not a full matrix):

| Example | cpython-venv | micropython | Notes |
|---------|--------------|-------------|-------|
| `pbm_create_new` | ok | — | prior batch |
| `pbm_simpletest` | ok | — | prior batch |
| `scroll_touch_test` | ok | — | prior batch |
| `testris` | ok | — | prior batch |
| `bmp565_scroll_sprite` | ok | — | prior batch |
| `scroll_touch_test_displaybuf` | ok | ok | was hang on cpython-venv |
| `displaybuf_blit` | ok | ok | was `AttributeError` on MP |
| `font_simpletest3` | ok | ok | graphics-cmod smoke |
| `displaybuf_simpletest` | ok | — | graphics-cmod smoke |

**graphics-cmod:** `036e9b4` / TestPyPI **`v0.0.3`** (publish in progress). Full `graphics.__all__` parity on MP, CPython, CircuitPython — see `.cursor/graphics_cmod_parity_report.md`.

---

## Remaining (next)

| # | Item | Notes |
|---|------|-------|
| 1 | **Re-run full matrix** | Baseline counts predate `4ca8e1b7`–`c695451f`; expect fewer cpython hangs/errors and MP `displaybuf_blit` pass |
| 2 | MP.exe post-loop / teardown | exit_3/exit_5/hang — 44 exit cells in stale matrix |
| 3 | Hang cluster (non-cpython) | MP.exe: `font_simpletest2`, `bmp565_sprite_transparent`, `displaysys_fill_rect_test`, etc. |
| 4 | LVGL kit teardown | deferred (`matrix=false`) |
| 5 | `pixel_sim_demos` fire effect | simulator flame looks wrong (NOTES todo) |

**Cleared since baseline:** cpython DisplayBuffer/`graphics_native` subclass; `scroll_touch_test_displaybuf` hang; MP `displaybuf_blit`; hang-cluster quit contract + SDL teardown path for desktop loop examples.

---

## Rules of thumb

1. Loop examples: call `runtime.poll()` before checking `quit_requested`.
2. Test harness: test-mode `_handle_quit` sets `quit_requested` and calls `stop_timer()` only — do **not** call `display.quit()` from the inject daemon thread (SDL deadlock with DisplayBuffer refresh).
3. DisplayBuffer loop examples: call `runtime.stop_timer()` before the poll loop so periodic refresh does not fight manual `show()` / `blit_rect`.
4. CPython test mode: wrapper uses `os._exit` after result to skip slow `SDL_Quit`; oneshot examples should not call `display_drv.quit()`.
5. `timer_simpletest`: `hard=False` only on micropython **librt** (unix), not MP.exe sdl2.
6. MP matrix from `src/`: `lib/` must precede `.frozen` (path.py prepend).

---

## Re-run command

```bash
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy .venv/bin/python tools/example_test_kit.py \
  --all-except-harness --order runtimes --no-unit-tests
```

Results: `.cursor/example_test_results.json`
