# Personal notes

Private working notes for this repo. Not part of the published docs.

## Todo

<!-- Add items when asked to "add … to my todo list". Use `- [ ]` checkboxes. -->

### add_ons

- [ ] Consolidate or merge `add_ons/` modules where possible (fewer top-level files)

### Peter Hinch GUIs (work as a set)

[nano-gui](https://github.com/peterhinch/micropython-nano-gui), [micro-gui](https://github.com/peterhinch/micropython-micro-gui), and [micropython-touch](https://github.com/peterhinch/micropython-touch) share `DisplayBuffer` / `framebuf` patterns — treat pydisplay integration for all three together (not one library at a time).

| Library | Upstream setup file | pydisplay `add_ons/` today |
|---------|---------------------|----------------------------|
| nano-gui | `color_setup.py` → `ssd` | `color_setup.py` (+ `ensure_nano_gui.py`, `uctypes.py`) |
| micro-gui | `hardware_setup.py` → `ssd`, `Display` | **missing** — need `hardware_setup.py` for buttons/encoder |
| micropython-touch | `touch_setup.py` → `ssd`, `display` | `hardware_setup.py` (**wrong name**; upstream renamed Dec 2024) |

- [ ] **Peter Hinch trio** — shared plan: mip install helpers, `DisplayBuffer`/`graphics.FrameBuffer` patches, CP shims, examples, and matrix coverage for nano-gui + micro-gui + micropython-touch
- [ ] Add `touch_setup.py` for micropython-touch; migrate content from misnamed `hardware_setup.py` (upstream expects `import touch_setup` first)
- [ ] Add proper `hardware_setup.py` for micro-gui (button/encoder `Display`; separate from touch)
- [ ] Merge `ensure_nano_gui.py` + `uctypes.py` into `color_setup.py` (nano-gui on CircuitPython); drop the separate files

### LVGL

- [ ] `lv_touch_test` on `micropython.exe` — fix LVGL/SDL timer queue / `micropython.schedule` overflow so it can re-enter matrix (currently `skip_runtimes`)
- [ ] `lv_touch_test` on `cpython-venv` — event-loop work (`matrix=false` today)
- [ ] Combine `display_driver.py` + `lv_utils.py` → `lv_runtime.py`
- [ ] `lv_runtime.py` — support multiple LVGL displays
- [ ] Ship `lv_runtime.py` with `lv_cpython_mod`, `lv_micropython_cmod`, and `lv_circuitpython_mod`
- [ ] Rename `eventsys.events.TOUCH` → `POINTER` (breaking; match LVGL `INDEV_TYPE.POINTER` naming)

### usdl2 & SDL

- [ ] `usdl2` all-C user module for MicroPython **and** CPython (like `graphics-cmod`; replace ctypes/ffi Python shims)
- [ ] Add `FFmpegFrameRecorder` / `open_frame_recorder` to `SDLDisplay` (already on `PGDisplay` via `displaysys`)

### displaysys & desktop

- [ ] **CircuitPython `SDLDisplay` forced software renderer** — `sdldisplay.py` downgrades accelerated GL on CP only (`SetRenderTarget` / `glFramebufferTexture2DEXT` fails on rotated render targets). On the same host MP unix uses SDL2 too; investigate whether this is a real CP/usdl2-binding difference or an outdated workaround — goal: HW-accelerated SDL on CP unix matching MP, or document the actual root cause
- [ ] Refactor `src/lib/board_config.py` for readability (same behavior; short comments OK)
- [ ] Rework `_hard_process_exit` in `sdldisplay.py` — used when `quit(force=True)` / kit teardown must skip SDL cleanup (`usdl2.process_exit`, `ffi` `_exit`, `os._exit` fallbacks); audit whether still needed after harness changes
- [ ] Make sure all desktop backends exit gracefully in `displaysys`

### Publishing & packaging

- [ ] Remove `pydisplay-bundle` everywhere — **first:** confirm all subpackages are on TestPyPI and [PyDevices/micropython-lib](https://github.com/PyDevices/micropython-lib); then drop bundle manifest, `packages/pydisplay-bundle.json`, Wokwi bundle, publish script bundle path, install manifests
- [ ] Make all PyDevices repo automations that publish to TestPyPI or micropython-lib also attach those artifacts as GitHub release assets per tag — see [testpypi-publish-audit.md](testpypi-publish-audit.md) (gap: none do today)

### Examples & demos

- [ ] **pdwidgets** — other agent lands `FrameBuffer.circle` first; then re-enable `widgets_*.py` in example matrix and PyScript gallery (`matrix=false` + `# pyscript skip: gallery` until stable)
- [ ] `pixel_sim_demos` fire effect — cellular flame does not look/behave correctly on the simulator (fix heat propagation / palette)
- [ ] Make all examples runnable on PyScript, then Jupyter notebook

### Platforms & hardware

- [ ] Get `pydisplay_android` working on desktop emulator
- [ ] Build MicroPython with LVGL, `graphics`, `displayif`, etc. for `board_configs/fbdisplay/esp32-p4-wifi6-touch-lcd-4b`
- [ ] Reorganize `board_configs` if it makes sense

### Frozen & standalone apps

- [ ] Frozen self-installer for MicroPython (Unix + `micropython.exe`) — see [frozen-self-installer-notes.md](frozen-self-installer-notes.md)
- [ ] Develop apps and freeze them into standalone executables — start with `spotapi_remote` in the spotapi repo

### graphics cmod

- [ ] Port RGB888 support from `graphics/_framebuf_plus.py` to the graphics cmod library

### multimer

- [ ] **multimer `hard=False` on CPython (librt)** — `schedule()` does not truly defer when librt delivers on the main thread: it runs the callback inline inside the signal handler (`src/lib/multimer/_schedule.py`). That broke `timer_simpletest` on cpython-venv when both timers used `hard=False` (hang before any output). **Done for now:** example-scoped fix — `hard=False` only when `sys.implementation.name == "micropython"` (heap locked in FFI); CPython keeps default `hard=True` (`timer_simpletest`, commit `c26ce285`). **Next bot:** core change in `multimer` — detect signal-handler / non-reentrant context on CPython and always queue callbacks (true soft delivery), then revisit examples and other hard timers (`console._tick`, `pdwidgets`, etc.). Deliberate, test on librt + LVGL; not urgent while examples use the MP-only guard.

### Tooling & ecosystem

- [ ] Re-run full desktop matrix (`tools/run_full_matrix_both_timer_modes.sh`) after other agent lands `FrameBuffer.circle` and MP.exe harness fixes; refresh `cross_runtime_report.md` counts — **then** start cloud agent on remaining matrix failures
- [ ] Add a GUI to the matrix test kit (`tools/example_test_kit.py`) — after cloud agent has cleared remaining matrix errors (circle/pdwidgets done before cloud agent starts)
- [ ] Verify `manifest.py` selection order in `~/github/cmods`
- [ ] Fork [figma2lvgl](https://github.com/khiyamiftikhar/figma2lvgl) and add option to output Python
- [ ] Change docs and scripts so cmods sub-repos don't mention or require cmods (personal workspace only — not required for other users); may need to move functionality out of cmods into sub-repos

### Done

- [x] Check `display_driver.py`, `lv_utils.py`, and `multimer` for possible refactor / optimizations
- [x] Find all globals in `src/lib` — see [src-lib-globals.md](src-lib-globals.md)
- [x] Trim `jupyter_notebook.ipynb` out of `pyscript.toml` (demo pages don't need it; bundled via `gen_repo_packages.py`)
- [x] Jupyter install notebook: add `board_config.py` to the `displaysys` TestPyPI package (may need default `board_config` to work without eventsys) — `src/lib/board_config.py` ships with core `displaysys` on next publish
- [x] `displaysys-*` backend subpackages on TestPyPI — v0.0.8: upload + `MICROPYTHON_LIB_DIR` fix; deps pgdisplay→pygame-ce, sdldisplay→usdl2; core `displaysys` ships `board_config.py`; no examples in wheels; removed `boarddisplay`
- [x] Ensure each `src/lib` package is installable alone — `tools/test_testpypi_standalone.sh` passes for core TestPyPI wheels + desktop backends; MCU `displaysys-*` on CPython need MP (e.g. `micropython.const` in busdisplay)
- [x] Settle on naming convention for all TestPyPI packages — see [testpypi-naming-convention.md](testpypi-naming-convention.md) (MIP short names; pip maps on pypi.org collision: `pydisplay-*`, `*-cmod`, `*-cpython`)
- [x] Audit PyDevices TestPyPI / micropython-lib publish workflows and wheel coverage — see [testpypi-publish-audit.md](testpypi-publish-audit.md) (native wheels OK; release assets still open; displaysys-* on TestPyPI from v0.0.8)
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
- [x] Verify which `mip` install methods install bare `.py` files vs precompiled `.mpy` files — see [mip-and-freeze-sources.md](mip-and-freeze-sources.md)
- [x] Move `SDL_desktop_size()` out of `usdl2` into `sdldisplay.py`; expose `SDL_GetDisplayUsableBounds` / `SDL_GetDesktopDisplayMode` on usdl2 instead
- [x] Fix `add_ons/README.md`: path setup is `import lib.path` (not `add_ons.add_path`)
- [x] Fix `add_ons/usdl2.py` docstring — ctypes on CPython unix+win32; ffi/uctypes on MicroPython unix
- [x] Update backend docs: drivers need `blit_rect`, `fill_rect`, and `pixel` — not only `show()` and `quit()`
- [x] Add `ruff` to `requirements-dev.txt`
- [x] Doc drift: Broker→Runtime in README/tests; DisplayDriver docstring + audit tag wording; add_ons README; display-ecosystem `runtime` contract; micropython.md TestPyPI `usdl2` note (no version pins)
- [x] SDL rescaling to fit the window on the screen is still too large in MicroPython — init `SDL_INIT_VIDEO` before querying usable desktop bounds (`SDL_INIT_EVERYTHING` left bounds at 0 on MP); ffi path uses `struct.unpack_from` (no `signed=` kw on MP)
