# Personal notes

Private working notes for this repo. Not part of the published docs.

## Todo

<!-- Add items when asked to "add … to my todo list". Use `- [ ]` checkboxes. -->

### Publishing & packaging

- [ ] Remove `pydisplay-bundle` everywhere — **first:** confirm all subpackages are on TestPyPI and [PyDevices/micropython-lib](https://github.com/PyDevices/micropython-lib); then drop bundle manifest, `packages/pydisplay-bundle.json`, Wokwi bundle, publish script bundle path, install manifests
- [ ] Make all PyDevices repo automations that publish to TestPyPI or micropython-lib also attach those artifacts as GitHub release assets per tag — see [testpypi-publish-audit.md](testpypi-publish-audit.md) (gap: none do today)

### displaysys & desktop

- [ ] SDL rescaling to fit the window on the screen is still too large in MicroPython
- [ ] Make sure all desktop backends exit gracefully in `displaysys`

### Examples & demos

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

- [ ] Port RGB888 support from `graphics/_framebuf.py` to the graphics cmod library

### multimer

- [ ] **multimer `hard=False` on CPython (librt)** — `schedule()` does not truly defer when librt delivers on the main thread: it runs the callback inline inside the signal handler (`src/lib/multimer/_schedule.py`). That broke `timer_simpletest` on cpython-venv when both timers used `hard=False` (hang before any output). **Done for now:** example-scoped fix — `hard=False` only when `sys.implementation.name == "micropython"` (heap locked in FFI); CPython keeps default `hard=True` (`timer_simpletest`, commit `c26ce285`). **Next bot:** core change in `multimer` — detect signal-handler / non-reentrant context on CPython and always queue callbacks (true soft delivery), then revisit examples and other hard timers (`console._tick`, `pdwidgets`, etc.). Deliberate, test on librt + LVGL; not urgent while examples use the MP-only guard.

### Tooling & ecosystem

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
- [x] Verify where `cmods/build_mp.sh` pulls `manifest.py` packages from — are they `.py` or `.mpy`? — see [mip-and-freeze-sources.md](mip-and-freeze-sources.md)
