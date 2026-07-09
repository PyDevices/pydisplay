# Personal notes

Private working notes for this repo. Not part of the published docs.

## Todo

<!-- Add items when asked to "add … to my todo list". Use `- [ ]` checkboxes. -->

- [ ] Frozen self-installer for MicroPython (Unix + `micropython.exe`) — see [frozen-self-installer-notes.md](frozen-self-installer-notes.md)

- [ ] Develop apps and freeze them into standalone executables — start with `spotapi_remote` in the spotapi repo

- [x] Check `display_driver.py`, `lv_utils.py`, and `multimer` for possible refactor / optimizations

- [x] Find all globals in `src/lib` — see [src-lib-globals.md](src-lib-globals.md)
- [x] Trim `jupyter_notebook.ipynb` out of `pyscript.toml` (demo pages don't need it; bundled via `gen_repo_packages.py`)
- [ ] Jupyter install notebook: add `board_config.py` to the `displaysys` TestPyPI package (may need default `board_config` to work without eventsys)
- [ ] Ensure each `src/lib` package is installable alone — no hard dependency on the other pydisplay libs being installed
- [ ] Make sure all desktop backends exit gracefully in `displaysys`
- [x] Compile MicroPython with `os.dupterm` enabled

- [ ] `bouncing_balls` has too many balls and runs too slow

- [x] `board_config` scaling for PGDisplay is too big — window doesn't fit the screen (auto-clamp in `PGDisplay`)

- [ ] Test kit only runs `tower_climb` in PGDisplay, not SDL2

- [ ] Combine all `pixel_sim_*` examples into a single file
  - [ ] Runnable through the sim or on the normal runtime by changing a single line (e.g. add `examples/pixel_sim` to the front of the path)

- [ ] Make `AGENTS.md` in cmods look for `AGENTS.md` at the root of all sub-repos

- [ ] Get `pydisplay_android` working on desktop emulator

- [ ] Build MicroPython with LVGL, `graphics`, `displayif`, etc. for `board_configs/fbdisplay/esp32-p4-wifi6-touch-lcd-4b`

- [ ] Make all PyDevices repo automations that publish to TestPyPI or micropython-lib also attach those artifacts as GitHub release assets per tag

- [ ] Make sure all PyDevices repo automations that publish to TestPyPI are publishing wheels for unix, windows, and Android

- [ ] Make `--no-os-dupterm` the default for Windows MicroPython builds only (so we don't have to pass it manually)

- [ ] Make all examples runnable on PyScript, then Jupyter notebook

- [ ] Port RGB888 support from `graphics/_framebuf.py` to the graphics cmod library

- [x] Port recent `src/lib/graphics` changes to `cmods/graphics` (`implementation()`, sentinels, `_framebuf_plus` default FrameBuffer)

- [ ] Rework `cmods/graphics` to be all C code, no Python wrappers

- [ ] Reorganize `board_configs` if it makes sense

- [x] Verify which `mip` install methods install bare `.py` files vs precompiled `.mpy` files — see [mip-and-freeze-sources.md](mip-and-freeze-sources.md)

- [x] Verify where `cmods/build_mp.sh` pulls `manifest.py` packages from — are they `.py` or `.mpy`? — see [mip-and-freeze-sources.md](mip-and-freeze-sources.md)

- [ ] Change docs and scripts so cmods sub-repos don't mention or require cmods (personal workspace only — not required for other users); may need to move functionality out of cmods into sub-repos

- [ ] **multimer `hard=False` on CPython (librt)** — `schedule()` does not truly defer when librt delivers on the main thread: it runs the callback inline inside the signal handler (`src/lib/multimer/_schedule.py`). That broke `timer_simpletest` on cpython-venv when both timers used `hard=False` (hang before any output). **Done for now:** example-scoped fix — `hard=False` only when `sys.implementation.name == "micropython"` (heap locked in FFI); CPython keeps default `hard=True` (`timer_simpletest`, commit `c26ce285`). **Next bot:** core change in `multimer` — detect signal-handler / non-reentrant context on CPython and always queue callbacks (true soft delivery), then revisit examples and other hard timers (`console._tick`, `pdwidgets`, etc.). Deliberate, test on librt + LVGL; not urgent while examples use the MP-only guard.
