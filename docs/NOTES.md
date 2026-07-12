# Personal notes

Private working notes for this repo. Not part of the published docs.

## Todo

<!-- Add items when asked to "add … to my todo list". Use `- [ ]` checkboxes. -->

### add_ons

- [ ] Consolidate or merge `add_ons/` modules where possible (fewer top-level files)

### LVGL

- [ ] Combine `display_driver.py` + `lv_utils.py` → `lv_runtime.py`
- [ ] `lv_runtime.py` — support multiple LVGL displays
- [ ] Ship `lv_runtime.py` with `lv_cpython_mod`, `lv_micropython_cmod`, and `lv_circuitpython_mod`
- [ ] Rename `eventsys.events.TOUCH` → `POINTER` (breaking; match LVGL `INDEV_TYPE.POINTER` naming)

### usdl2 & SDL

- [ ] `usdl2` all-C user module for MicroPython **and** CPython (like `graphics-cmod`; replace ctypes/ffi Python shims)

### displaysys & desktop

- [ ] **CircuitPython `SDLDisplay` forced software renderer** — `sdldisplay.py` downgrades accelerated GL on CP only (`SetRenderTarget` / `glFramebufferTexture2DEXT` fails on rotated render targets). On the same host MP unix uses SDL2 too; investigate whether this is a real CP/usdl2-binding difference or an outdated workaround — goal: HW-accelerated SDL on CP unix matching MP, or document the actual root cause

### Publishing & packaging

- [ ] Remove `pydisplay-bundle` everywhere — **first:** confirm all subpackages are on TestPyPI and [PyDevices/micropython-lib](https://github.com/PyDevices/micropython-lib); then drop bundle manifest, `packages/pydisplay-bundle.json`, Wokwi bundle, publish script bundle path, install manifests
- [ ] Make all PyDevices repo automations that publish to TestPyPI or micropython-lib also attach those artifacts as GitHub release assets per tag — see [testpypi-publish-audit.md](../.cursor/testpypi-publish-audit.md) (gap: none do today)

### Examples & demos

- [ ] Audit all examples: for each, note what it demonstrates and how it helps users and/or the matrix test kit; decide keep, consolidate, or delete. Many were small development probes (e.g. scrolling/rotation for touch→screen coords) that may have limited value now that those bugs are fixed; others (e.g. `font_simpletest*.py`) overlap but show different methods with different speed/resource/transparency tradeoffs — keep distinct approaches where that teaching value matters. Large surface area, but a structured pass should be relatively quick

### Platforms & hardware

- [ ] Get `pydisplay_android` working on desktop emulator
- [ ] Build MicroPython with LVGL, `graphics`, `displayif`, etc. for `board_configs/fbdisplay/esp32-p4-wifi6-touch-lcd-4b`
- [ ] Reorganize `board_configs` if it makes sense

### Frozen & standalone apps

- [ ] Frozen self-installer for MicroPython (Unix + `micropython.exe`) — see [frozen-self-installer-notes.md](../.cursor/frozen-self-installer-notes.md)
- [ ] Develop apps and freeze them into standalone executables — start with `spotapi_remote` in the spotapi repo

### multimer

- [ ] **multimer `hard=False` on CPython (librt)** — `schedule()` does not truly defer when librt delivers on the main thread: it runs the callback inline inside the signal handler (`src/lib/multimer/_schedule.py`). **Next bot:** core change in `multimer` — detect signal-handler / non-reentrant context on CPython and always queue callbacks (true soft delivery), then revisit examples and other hard timers (`console._tick`, `pdwidgets`, etc.). Deliberate, test on librt + LVGL.

### MCU optimization

(Multimer is out of scope for this work.)

- [ ] Optimize `lib/graphics` first, then `graphics_cmod`, for microcontrollers — memory, storage, and speed
- [ ] Same MCU optimization pass for `eventsys` and `displaysys` (consecutively or concurrently with graphics)

### Tooling & ecosystem

- [ ] Remove redundant and consolidate overlapping tools under `tools/`; remove any unnecessary tools that are no longer needed or used
- [ ] Add a GUI to the matrix test kit (`tools/example_test_kit.py`)
- [ ] Fork [figma2lvgl](https://github.com/khiyamiftikhar/figma2lvgl) and add option to output Python
- [x] Change docs and scripts so owned cmod repos don't mention or require the personal cmods workspace (sibling-clone + raw `make` / per-repo build scripts are primary; cmods optional)

### Done

- [x] Make all examples runnable on PyScript, then Jupyter notebook
- [x] Eliminate `src/lib/env_util.py` — moved `env_bool` / `env_set` into `displaysys`
- [x] `pixel_sim_demos` fire effect — Doom-style heat rise with height-scaled cooling, gappy embers, black→white palette (was blurry average + cooling=3 that filled a short 16-row grid solid)
- [x] Make sure all desktop backends exit gracefully in `displaysys`
- [x] Fix cmods `manifest.py` / `build_mp.sh` frozen-manifest selection — `build_mp.sh` exports `FROZEN_MANIFEST_UPSTREAM` to the MicroPython freeze file for the build; static `cmods/manifest.py` includes cmod siblings then that path (no generated wrapper). Verified via `cmods/scripts/verify_frozen_manifest_parity.sh`: unix standard/coverage, windows dev, webassembly pyscript, esp32 ESP32_GENERIC_P4/C6_WIFI + M5STACK_ATOM, rp2 RPI_PICO
- [x] Verify `manifest.py` selection order in `~/github/cmods` — **was incorrect;** fixed (see above)
- [x] Remove redundant and consolidate overlapping scripts under `scripts/`; remove unused ones — deleted `migrate_*_to_runtime.py` and `generate_epaper_board_configs.py` (use `generate_board_configs.py` / `--kind epaper`); moved `tools/make_color_icons.py` → `scripts/assets_make_color_icons.py`; docs/tests updated
- [x] List all `.py` files under `board_configs/`, `drivers/`, and `src/` that read environment variables; remove env access where unnecessary. Keep `src/lib/board_config` reading the env for the default `timer_async` value; prefer no other scripts in those directories access envars — inventory done; removed `PGDisplay.open_frame_recorder_from_env` (callers use `open_frame_recorder(path, fps=…)`). Example env use left for examples audit
- [x] Check `display_driver.py`, `lv_utils.py`, and `multimer` for possible refactor / optimizations
- [x] Find all globals in `src/lib` — see [src-lib-globals.md](../.cursor/src-lib-globals.md)
- [x] Trim `jupyter_notebook.ipynb` out of `pyscript.toml` (demo pages don't need it; bundled via `gen_repo_packages.py`)
- [x] Jupyter install notebook: add `board_config.py` to the `displaysys` TestPyPI package (may need default `board_config` to work without eventsys) — `src/lib/board_config.py` ships with core `displaysys` on next publish
- [x] `displaysys-*` backend subpackages on TestPyPI — v0.0.8: upload + `MICROPYTHON_LIB_DIR` fix; deps pgdisplay→pygame-ce, sdldisplay→usdl2; core `displaysys` ships `board_config.py`; no examples in wheels; removed `boarddisplay`
- [x] Ensure each `src/lib` package is installable alone — `tools/test_testpypi_standalone.sh` passes for core TestPyPI wheels + desktop backends; MCU `displaysys-*` on CPython need MP (e.g. `micropython.const` in busdisplay)
- [x] Settle on naming convention for all TestPyPI packages — see [testpypi-naming-convention.md](../.cursor/testpypi-naming-convention.md) (MIP short names; pip maps on pypi.org collision: `pydisplay-*`, `*-cmod`, `*-cpython`)
- [x] Audit PyDevices TestPyPI / micropython-lib publish workflows and wheel coverage — see [testpypi-publish-audit.md](../.cursor/testpypi-publish-audit.md) (native wheels OK; release assets still open; displaysys-* on TestPyPI from v0.0.8)
- [x] Make displaysys only print `requires_byteswap` when it is True
- [x] SDL/PG batch mode — defer compositor `render()` until `show()` (texture updates batched in `blit_rect` / `fill_rect`)
- [x] `board_config` scaling for PGDisplay is too big — window doesn't fit the screen (auto-clamp in `PGDisplay`)
- [x] `bouncing_balls` has too many balls and runs too slow — cap 30, scale with area // 8000 (was // 3000, max 100)
- [x] Test kit only runs `tower_climb` in PGDisplay, not SDL2 — `example_runtimes.toml` sets `display_backend = SDLDisplay` for desktop runtimes; matrix shows `tower_climb | SDLDisplay, ok`
- [x] Combine all `pixel_sim_*` examples into a single file — `pixel_sim_demos.py` with `DEMO` selector; swap `pixel_sim` vs `board_config` import for sim vs hardware
- [x] Compile MicroPython with `os.dupterm` enabled
- [x] Make `--no-os-dupterm` the default for Windows MicroPython builds only (so we don't have to pass it manually)
- [x] Make `AGENTS.md` in cmods look for `AGENTS.md` at the root of all sub-repos
- [x] Port recent `src/lib/graphics` changes to `cmods/graphics` (`implementation()`, sentinels, `_framebuf_plus` default FrameBuffer)
- [x] Rework `cmods/graphics` to be all C code, no Python wrappers — full `graphics.__all__` parity on MP, CPython, and CircuitPython (`036e9b4`). CP rebuild: `apply_cp_unix_graphics_patches.sh` then `build_cp.sh --port unix --variant coverage`. See `.cursor/graphics_cmod_parity_report.md`
- [x] `cmods/graphics` publish to TestPyPI — v0.0.2 tagged and published (14 wheels on TestPyPI)
- [x] Port RGB888 support from `graphics/_framebuf_plus.py` to the graphics cmod library — already in cmod (`GFX_RGB888` + rgb888 pixel ops in `gfx_framebuffer.c`); `_framebuf_plus` Python path kept for non-cmod fallbacks
- [x] Verify which `mip` install methods install bare `.py` files vs precompiled `.mpy` files — see [mip-and-freeze-sources.md](../.cursor/mip-and-freeze-sources.md)
- [x] Move `SDL_desktop_size()` out of `usdl2` into `sdldisplay.py`; expose `SDL_GetDisplayUsableBounds` / `SDL_GetDesktopDisplayMode` on usdl2 instead
- [x] Fix `add_ons/README.md`: path setup is `import lib.path` (not `add_ons.add_path`)
- [x] Fix `add_ons/usdl2.py` docstring — ctypes on CPython unix+win32; ffi/uctypes on MicroPython unix
- [x] Update backend docs: drivers need `blit_rect`, `fill_rect`, and `pixel` — not only `show()` and `quit()`
- [x] Add `ruff` to `requirements-dev.txt`
- [x] Doc drift: Broker→Runtime in README/tests; DisplayDriver docstring + audit tag wording; add_ons README; display-ecosystem `runtime` contract; micropython.md TestPyPI `usdl2` note (no version pins)
- [x] SDL rescaling to fit the window on the screen is still too large in MicroPython — init `SDL_INIT_VIDEO` before querying usable desktop bounds (`SDL_INIT_EVERYTHING` left bounds at 0 on MP); ffi path uses `struct.unpack_from` (no `signed=` kw on MP)
- [x] Refactor `src/lib/board_config.py` for readability (same behavior; short comments OK)
- [x] Re-run full desktop matrix and refresh `.cursor/cross_runtime_report.md` (2026-07-10: 292/294 sync, 290/294 async executed)
- [x] **pdwidgets rework** — bug fixes (competing timer, `tick()` coalescing), hardening, `pct` perf, new widgets (`Card`, `Row`/`Column`, `Badge`, `Switch`, `NumberStepper`, `TextInput`, `Dropdown`, `Dialog`), visual design system, 3 showcase examples; `widgets_*.py` re-enabled in the example matrix and PyScript gallery (PR #62)
