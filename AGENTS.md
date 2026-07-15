# AGENTS.md

## Cursor Cloud specific instructions

PyDisplay is a pure-Python, dependency-light graphics/input/timer library that
runs on CPython, MicroPython, and CircuitPython. There is no build step; source
lives under `src/lib` (packages) and `src/examples` (demos). `web/pyscript/src`
is a symlink to `../../src`, so editing `src/` updates the PyScript gallery too.

### Environment

- **Cursor Cloud (multi-repo workspace):** do not use a local
  `.cursor/environment.json` in this repo. The canonical cloud environment lives
  in [PyDevices/.github](https://github.com/PyDevices/.github) — start Cloud
  Agents from that repo (or `cmods`) with the saved **Pydevices Cloud
  Workspace** environment. Its install command is
  `bash scripts/cloud-workspace-install.sh` (relative to the `.github` checkout),
  which symlinks `/agent/repos/*` into `~/gh/pydevices/`. See
  [AGENTS.md there](https://github.com/PyDevices/.github/blob/main/AGENTS.md).
- Use the repo-root virtualenv at `.venv` for all Python tooling
  (`.venv/bin/python`, `.venv/bin/ruff`). The system `python3` has no project
  dependencies installed.
- Only the `cpython-venv` runtime is available here. `micropython`,
  `micropython.exe`, `circuitpython`, and `python.exe` are installed on the system path, so
  cross-runtime matrices can exercise all 5.  ./tools/jupyter.sh and ./tools/pyscript.sh aid
  development in Jupyter Notebook and PyScript respectively.
- The desktop display backend on CPython on Windows is `PGDisplay` (pygame-ce; `import pygame`).
  `pygame-ce` is installed on top of `requirements-dev.txt` (it is intentionally
  not listed there — SDL2 is the documented primary and pygame-ce is the fallback).

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

- **Read [`.cursor/example-runtimes.md`](.cursor/example-runtimes.md)
  first** — it is the source of truth for the cross-runtime example test system
  (runtimes, prerequisites, the example contract, the matrix commands, and
  debugging). The canonical runtime list is
  [`tools/example_runtimes.toml`](tools/example_runtimes.toml) and per-example
  metadata is [`tools/example_test_manifest.toml`](tools/example_test_manifest.toml).
- The cross-runtime example harness is `tools/example_test_kit.py`. To run the
  CPython matrix headlessly, set dummy SDL drivers so pygame or SDL needs no display:
  `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy .venv/bin/python tools/example_test_kit.py --no-unit-tests --only-runtime cpython-venv`
  Use `--only-example <name> ...` to scope. Results are written to
  `.cursor/example_test_results.json` (gitignored).
- A real X display is also available at `DISPLAY=:1` (xfce desktop). Running an
  example there (without the dummy SDL driver) opens a real pygame window titled
  `"<impl> on <platform>"`, which can be screenshotted/recorded with `ffmpeg`
  (`-f x11grab -i :1`).
- **Xvfb (optional):** keep dummy SDL as the default for headless matrix/smoke.
  Use `xvfb-run -a …` (no `SDL_VIDEODRIVER=dummy`) when you need a real X11/SDL
  window path without `:1` — e.g. native screenshots/recording, or catching
  “works on dummy, fails on real X” bugs. Do not change the tools scripts to
  require it; wrap the command when useful. PyScript/Playwright tools do not
  need Xvfb.
- Known pre-existing example failures on CPython (not environment issues to
  "fix"): `nano_gui_simpletest` needs the matching Hinch `gui/` package.
  `tools/png_test.py` in **pdwidgets** (PNG probe) needs `PDWIDGETS_PNG_DIR` / material-design-icons and a sibling pydisplay checkout.
- **`palettes` / `pdwidgets` sibling repos** (`hello`, `color_test`, `feathers`,
  `graphics_simpletest`, `palettes_demo`, `widgets_*`, … import `palettes` and/or
  `pdwidgets`). These are source-only PyDevices repos, **not** pip packages — the
  PyPI project literally named `palettes` is an unrelated "random hex color"
  library, so do **not** `pip install palettes`. They normally arrive as
  repositoryDependencies under `/agent/repos/{palettes,pdwidgets}` (symlinked into
  `~/gh/pydevices/`); if that clone is missing, clone
  `github.com/PyDevices/{palettes,pdwidgets}` into a writable dir and put their
  `src` dirs on the venv path (e.g. a `*.pth` in `.venv/lib/*/site-packages`
  listing `<repo>/palettes/src` and `<repo>/pdwidgets/src`, or `PYTHONPATH`).
  Quick setup: `bash scripts/setup_sibling_repos.sh` (clones current `main` and
  writes `.pth` files). The example harness (`tools/sibling_repos.py`) auto-discovers
  the same paths for matrix runs.
  `pdwidgets` also needs pydisplay's `src/lib` on path (the example harness adds it).
- Cross-runtime binaries: `micropython`/`circuitpython` resolve via `PATH` →
  `~/bin` → committed `repo:bin/` (see `bin/README.md`), so the matrix runs those
  two even when they are not on the system `PATH`. `micropython.exe` / `python.exe`
  are Windows binaries and cannot run in the Linux cloud sandbox.
- **PyScript hangs / multimer / WASM:** read
  [`.cursor/pyscript-troubleshooting.md`](.cursor/pyscript-troubleshooting.md)
  before poking the IDE browser. Prefer Playwright helpers
  (`tools/ps_debug.py`, `ps_shot.py`) and console/CDP capture — sync
  `sleep_ms` on the main thread often wedges `page.evaluate` and screenshots.

### `PYDISPLAY_TIMER_ASYNC` (default `board_config`)

`src/lib/board_config.py` sets `runtime.timer_async` when constructing
`eventsys.Runtime`. **Examples never read this variable** — only the library
board_config (and test harnesses that call `displaysys.env_set`).

| Host branch | `timer_async` |
|-------------|---------------|
| PyScript (`PSDisplay`) | always `True` |
| Jupyter (`JNDisplay`) | always `True` |
| PG/SDL desktop | `False` by default; host override below |
| MCU board_configs | whatever that board sets (no shell env needed) |

**Desktop host override** (where `getenv` exists): set **`PYDISPLAY_TIMER_ASYNC`**
before `board_config` is imported. Truthy: `1`, `true`, `yes`, `on`. Falsey:
`0`, `false`, `no`, `off`. Helper: `displaysys.env_bool`.

**Preferred for agents / matrix:** pass wrapper `--timer-async` (the kit and
`run_desktop_matrix_concurrent.py` do this). That uses `env_set` and works for
Windows PE under WSL without relying on OS environ. Shell export remains a
valid host shortcut:

```bash
# kit inherits host env and forwards --timer-async for PE/WSL
PYDISPLAY_TIMER_ASYNC=1 SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \
  .venv/bin/python tools/example_test_kit.py --no-unit-tests --only-runtime cpython-venv
```

`lv_test_timer.py` follows `runtime.timer_async` and does not set env vars.
To force async on desktop for that example (or the LVGL kit), set
`PYDISPLAY_TIMER_ASYNC=1` on the parent process before launch, or use a kit that
passes `--timer-async`.

**`micropython.exe` matrix:** no `threading` / `_thread`. `example_test_wrapper.py` uses a
`Runtime.poll` deadline quit (not a multimer SDL quit timer). With
`pydisplay_test_mode.ENABLED`, `Runtime` skips auto-refresh wiring so examples
that call `show()` themselves avoid a competing SDL refresh timer.

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
- Test LVGL timers with `tools/lv_timer_test_kit.py` (modes: `sync`, `async`).
  Headless: `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy .venv/bin/python tools/lv_timer_test_kit.py --only cpython-venv`.
- Non-obvious: the sync `multimer.Timer` backend on CPython/Linux delivers via a
  main-thread signal handler. LVGL is not re-entrant, so the app loop must not
  touch LVGL/pygame concurrently while that tick runs; LVGL examples use
  cooperative deadline/`time.sleep` (sync) or `asyncio.sleep` (async). The LVGL
  timer kit covers dedicated click checks — its daemon-thread quit injection is
  incompatible with the generic example matrix for some ports.
- **`multimer` is fragile** — read [`.cursor/rules/multimer-fragile.mdc`](.cursor/rules/multimer-fragile.mdc)
  before editing `src/lib/multimer/` (thinking model required, small diffs, revert failures).
