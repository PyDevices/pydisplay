# AGENTS.md

## Cursor Cloud specific instructions

This repo is the PyDevices examples, documentation, and PyScript gallery. The
shareable product libraries live in sibling `pydevices`. There is no
build step for examples. `web/pyscript/src` is a symlink to `../../src`, so
editing `src/` updates the PyScript gallery too.

### Environment

`displaydev`, `audiodev`, optional `eventsys`, `multimer`, `events`, `keys`,
and portable hardware utilities live in sibling
[pydevices](https://github.com/PyDevices/pydevices), which
also owns TestPyPI/MIP publishing. Non-LVGL examples explicitly import
`runtime` from `app_runtime`; LVGL examples import it from `display_driver`.
Board configs never own a runtime. `AutoDisplay` is imported from
`displaydev.auto` only.

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
- Desktop matrices use repo `.venv` (`cpython-venv`) plus interpreters on
  `PATH` / `bin/` (`micropython`, `circuitpython`, and when present
  `micropython.exe` / `python.exe`).   `./bin/jupyter.sh`, `./bin/pyscript.sh`, and
  `android.sh` (`pydevices-android-template/scripts/`, usually via `~/bin`) aid
  Jupyter, PyScript, and Android (adb stage onto `org.pydevices.launcher`;
  cwd paths like CLI Python — not PyScript gallery). Opt-in matrix:
  `tools/example_test_kit.py --only-runtime android …`.
- The desktop display backend on CPython on Windows is `PGDisplay` (pygame-ce;
  `import pygame`). Prefer `python.exe` for PG work. Do **not** install pygame-ce
  into `.venv` / system `python3` on this laptop — those stay SDL-primary;
  `board_config` falls back to `SDLDisplay` when pygame-ce's public
  `pygame.Window` API is missing. `pygame-ce` is intentionally not in
  `requirements-dev.txt`.

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

- **Read [`tools/README.md` — Example test matrix](tools/README.md#example-test-matrix)
  first** — agent runbook for the cross-runtime example test system. Canonical
  runtime list: [`tools/example_runtimes.toml`](tools/example_runtimes.toml);
  per-example metadata: [`tools/example_test_manifest.toml`](tools/example_test_manifest.toml).
- **Preferred thorough gate:** example-by-example with **all selected runtimes
  in parallel** (`--jobs 0`): **5** desktop for sync, **7** for async; both
  `PYDEVICES_TIMER_ASYNC=0` and `=1`, `--fail-fast`, line-buffered live log,
  fix after a failed example wave then resume — see
  [Preferred method](tools/README.md#preferred-method-parallel-runtimes-fail-fast-both-timer-modes)
  and [Windows PE under WSL](tools/README.md#windows-pe-under-wsl).
  Do **not** forward `SDL_*` to `*.exe` (PE windows should appear; unix stays
  headless from the shell export). A PE `hang` with a live window means quit
  failed, not that PE failed to start. `--curated-only` is smoke only.
- `--only-example` / `--only-runtime` take **space-separated** ids on one flag
  (`--only-runtime circuitpython python.exe`). Repeating the flag keeps only
  the last list — see [tools/README.md](tools/README.md#matrix-commands).
- Quick headless CPython smoke:

  ```bash
  SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \
    .venv/bin/python tools/example_test_kit.py --no-unit-tests --only-runtime cpython-venv
  ```

- PyScript hangs / CDP: prefer Playwright helpers and
  [Headless / CDP troubleshooting](docs/guides/pyscript.md#headless--cdp-troubleshooting)
  before poking the IDE browser.

### `PYDEVICES_TIMER_ASYNC` (agents / matrix)

Host defaults and env semantics:
[Runtime — `timer_async`](docs/concepts/runtime.md#timer_async-in-srclibboard_configpy).
Examples never read this variable — only library `board_config` and harnesses
that call `displaydev.env_set`.

**Preferred for agents / matrix:** pass wrapper `--timer-async` (the example
kit does this). That uses `env_set` and works for Windows PE under WSL without
relying on OS environ. Shell export remains a valid host shortcut:

```bash
PYDEVICES_TIMER_ASYNC=1 SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \
  .venv/bin/python tools/example_test_kit.py --no-unit-tests --only-runtime cpython-venv
```

`lv_test_timer.py` follows `runtime.timer_async` and does not set env vars.
To force async on desktop for that example (or the LVGL kit), set
`PYDEVICES_TIMER_ASYNC=1` on the parent process before launch, or use a kit that
passes `--timer-async`.

**`micropython.exe` matrix:** no `threading` / `_thread`. See
[tools/README.md — Interpreters and binaries](tools/README.md#interpreters-and-binaries).

### Architecture note: timers and refresh

- Non-LVGL examples opt into `eventsys.Runtime` in `src/utils/app_runtime.py`.
  LVGL's frozen/bundled `display_driver` owns an independent coordinator and
  does not import `eventsys`. Both consume neutral board-config callables and
  use `multimer`; display drivers remain policy-free.

### MCU: no `_thread` for network / blocking work

Full guidance:
[MicroPython — Background work (`_thread`)](docs/platforms/micropython.md#background-work-_thread).
App pattern: queue work and drain on the main tick — see `roku_widgets` /
`roku_lvgl` / `roku_graphics` (`_run_bg` + `_drain_bg`). Do not “fix” this in
`eventsys` with speculative reentrancy guards — keep the pattern in the app.

### LVGL

- Install the CPython LVGL binding from TestPyPI (import name `lvgl`):
  `.venv/bin/pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ pydevices-lvgl`
  (see https://github.com/PyDevices/lvgl-python). The update script installs it.
- `display_driver` (frozen in MP/CP LVGL firmwares; bundled with `pydevices-lvgl`)
  owns the LVGL `event_loop` (tick via `runtime.on_tick`, `asyncio` from
  `multimer`) and claims runtime display refresh so LVGL presents frames from
  `task_handler`. SoT: [lvgl-bindings](https://github.com/PyDevices/lvgl-bindings)
  `python/display_driver.py` — not shipped from this repo.
- Test LVGL timers with `tools/lv_timer_test_kit.py` (modes: `sync`, `async`).
  Headless: `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy .venv/bin/python tools/lv_timer_test_kit.py --only cpython-venv`.
- Non-obvious: the sync `multimer.Timer` backend on CPython/Linux delivers via a
  main-thread signal handler. LVGL is not re-entrant, so the app loop must not
  touch LVGL/pygame concurrently while that tick runs; LVGL examples use
  cooperative deadline/`time.sleep` (sync) or `asyncio.sleep` (async). The LVGL
  timer kit covers dedicated click checks — its daemon-thread quit injection is
  incompatible with the generic example matrix for some ports.
- **`multimer` is fragile** — before editing hardware `lib/multimer/`, read
  [multimer concepts](docs/concepts/multimer.md) and follow the local Cursor
  rule `multimer-fragile` (thinking model, small diffs, revert failures). Do not
  duplicate that rule text in this repo.

### MCU board bring-up (displayif / soft-reset)

When bringing up or debugging a MicroPython `board_configs/fbdisplay/*` board
that uses displayif (`mipidsi`, `rgbframebuffer`, `picodvi`, …), especially with
LVGL and mpftp soft-reset:

- Soft-reset + re-import is the acceptance test (no hard reset).
- Prefer `mip.install` over Wi‑Fi for large Python trees; mpftp for thin files
  and firmware.
- Symptom table, wrap architecture, and bring-up methods live in the sibling
  displayif repo:
  [`SOFT_RESET_AND_BRINGUP.md`](https://github.com/PyDevices/displayif/blob/main/docs/SOFT_RESET_AND_BRINGUP.md)
  (local: `../cmods/displayif/docs/SOFT_RESET_AND_BRINGUP.md` or
  `~/gh/pydevices/cmods/displayif/…`). Start at displayif `AGENTS.md`.
- Do not leave flash-backed debug logs on the touch/refresh path (looks like
  flicker). Fix displayif/bindings root causes rather than board_config
  workarounds.
