# AGENTS.md

## Cursor Cloud specific instructions

PyDisplay is a pure-Python, dependency-light graphics/input/timer library that
runs on CPython, MicroPython, and CircuitPython. There is no build step; source
lives under `src/lib` (packages) and `src/examples` (demos). `web/pyscript/src`
is a symlink to `../../src`, so editing `src/` updates the PyScript gallery too.

### Environment

- Use the repo-root virtualenv at `.venv` for all Python tooling
  (`.venv/bin/python`, `.venv/bin/ruff`). The system `python3` has no project
  dependencies installed.
- Only the `cpython-venv` runtime is available here. `micropython`,
  `micropython.exe`, `circuitpython`, and `python.exe` are **not** installed, so
  cross-runtime matrices only exercise CPython.
- The desktop display backend on CPython is `PGDisplay` (pygame). `pygame` and
  `ruff` are installed on top of `requirements-dev.txt` (they are intentionally
  not listed there — SDL2 is the documented primary and pygame is the fallback).

### Tests and lint

- Unit tests (stdlib `unittest`, no third-party runner needed):
  `.venv/bin/python -m unittest discover -s tests`
- Lint/format: `.venv/bin/ruff check src tests board_configs` and
  `.venv/bin/ruff format`. Note `pyproject.toml` **excludes `src/examples/**`**
  (and a few others) from ruff, so example files are not linted/formatted; do not
  be surprised when `ruff format --check` on an example path reports a diff.
- The pre-commit hooks (`.pre-commit-config.yaml`) are `ruff-check`,
  `ruff-format` (python/pyi only), and `nbstripout` for notebooks. `ruff` does
  **not** lint `*.ipynb` under the hook config, so pre-existing notebook findings
  from `ruff check` on the whole tree can be ignored.

### Running examples headlessly (GUI smoke tests)

- The cross-runtime example harness is `tools/example_test_kit.py`. To run the
  CPython matrix headlessly, set dummy SDL drivers so pygame needs no display:
  `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy .venv/bin/python tools/example_test_kit.py --no-unit-tests --only-runtime cpython-venv`
  Use `--only-example <name> ...` to scope. Results are written to
  `.cursor/example_test_results.json` (gitignored).
- A real X display is also available at `DISPLAY=:1` (xfce desktop). Running an
  example there (without the dummy SDL driver) opens a real pygame window titled
  `"<impl> on <platform>"`, which can be screenshotted/recorded with `ffmpeg`
  (`-f x11grab -i :1`).
- Known pre-existing example failures on CPython (not environment issues to
  "fix"): `lv_test_timer_*`/`lv_touch_test` need `lvgl` (not installed),
  `nano_gui_simpletest` needs the `gui` package, `png_test` needs
  `PYDISPLAY_PNG_DIR`, and `testris`/`bmp565_scroll_sprite`/`lv_test_timer_async`
  fail identically on `main` (unrelated to timer/display code).

### Architecture note: timers and refresh

- The single shared periodic timer is owned by `eventsys.Runtime`
  (`Runtime.on_tick` / `stop_timer`), not by display drivers. `board_config`
  constructs `eventsys.Runtime(display=display_drv, ...)` which wires periodic
  refresh when `display_drv.needs_refresh` is true. `displaysys` drivers only
  `show()`/`deinit()` and declare `needs_refresh`; `multimer` stays
  display-agnostic. GUI layers claim presentation via
  `runtime.claim_display_refresh()` (LVGL via `add_ons/display_driver.py`).

### LVGL

- Install the CPython LVGL binding from TestPyPI (import name `lvgl`):
  `.venv/bin/pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ lvgl-cpython`
  (see https://github.com/PyDevices/lv_cpython_mod). The update script installs it.
- `add_ons/lv_utils.py` subscribes its LVGL tick to the runtime's shared timer
  (`runtime.on_tick`) and imports `asyncio` from `multimer`; `add_ons/display_driver.py`
  claims runtime display refresh so LVGL presents frames from `task_handler`.
- Test LVGL timers with `tools/lv_timer_test_kit.py` (modes: `sync`, `async` —
  there is no pump/no_pump). Headless: `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy .venv/bin/python tools/lv_timer_test_kit.py --only cpython-venv`.
- Non-obvious: the sync `multimer.Timer` backend on CPython/Linux delivers via a
  main-thread signal handler. LVGL is not re-entrant, so the app loop must not
  touch LVGL/pygame concurrently (just `sleep_ms(0)`); the LVGL timer examples
  are therefore excluded from the generic example matrix (`matrix = false`) — its
  daemon-thread quit injection is incompatible — and are covered by the kit
  instead. In this VNC/SDL environment, external desktop mouse clicks do not reach
  the pygame window; use the kit's event-queue injection to exercise input.
