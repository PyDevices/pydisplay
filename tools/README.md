# pydisplay `tools/`

Developer workflow only — local servers, test harnesses, and IDE typings. For repo maintenance see [`scripts/README.md`](../scripts/README.md).

## PyScript / Jupyter launchers

| Script | Purpose |
|--------|---------|
| [`serve.py`](serve.py) | HTTP server with Cross-Origin-Isolation headers |
| [`pyscript.sh`](../bin/pyscript.sh) | Open one example in the browser — `./bin/pyscript.sh calculator` |
| [`jupyter.sh`](../bin/jupyter.sh) | JupyterLab or Cursor notebooks — `./bin/jupyter.sh calculator` |

From repo root:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt   # playwright, pytest (optional)
.venv/bin/playwright install chromium           # headless PyScript matrix

python tools/serve.py
# http://127.0.0.1:8000/web/pyscript/index.html
# http://127.0.0.1:8000/web/pyscript/micropython.html?modules=calc_graphics,calc_engine

./bin/pyscript.sh calculator
./bin/jupyter.sh calculator --cursor
```

See [Run the notebook interactively](../docs/platforms/jupyter-run.md) and [PyScript local development](../docs/guides/pyscript.md).

## Input / keypad probe

| Script | Purpose |
|--------|---------|
| [`input_probe.py`](input_probe.py) | Cross-backend keyboard/keypad diagnostic + selftests (eventsys + optional LVGL map) |

```bash
python tools/input_probe.py --selftest
cd src && micropython ../tools/input_probe.py --selftest --lvgl
cd src && python ../tools/input_probe.py   # interactive; focus the window
```

## PyScript headless debug (Playwright)

| Script | Purpose |
|--------|---------|
| [`ps_debug.py`](ps_debug.py) | CDP console + network probe for a harness/load URL |
| [`ps_shot.py`](ps_shot.py) | Timed screenshot with a hard kill if Chromium stalls |

Agent-oriented guide: [PyScript local development](../docs/guides/pyscript.md)
(including [Headless / CDP troubleshooting](../docs/guides/pyscript.md#headless--cdp-troubleshooting)).

```bash
python tools/serve.py   # separate terminal
.venv/bin/python tools/ps_debug.py \
  'http://127.0.0.1:8000/web/pyscript/harness.html?modules=calc_graphics,calc_engine&autotest=1' 20
```

## Example test matrix

**Source of truth** for the cross-runtime example test system: this section
(workflow), [`example_runtimes.toml`](example_runtimes.toml) (runtime command
templates), and [`example_test_manifest.toml`](example_test_manifest.toml)
(per-example metadata). **Platform** is the product category (see
[Portability & platforms](../docs/platforms/index.md)); **runtime** is the
concrete launcher used in automation.

| Script | Purpose |
|--------|---------|
| [`example_test_kit.py`](example_test_kit.py) | Cross-runtime example matrix |
| [`example_test_manifest.toml`](example_test_manifest.toml) | Per-example metadata |
| [`example_runtimes.toml`](example_runtimes.toml) | Runtime command templates |
| [`sibling_repos.py`](sibling_repos.py) | Discover sibling `lib/` paths for matrix runs |

### Unit tests first (default gate)

```bash
.venv/bin/python -m unittest discover -s tests
```

### Matrix commands

```bash
# Curated set across available runtimes
.venv/bin/python tools/example_test_kit.py --curated-only

# Scope
.venv/bin/python tools/example_test_kit.py --only-example calculator --only-runtime micropython
.venv/bin/python tools/example_test_kit.py --no-unit-tests --only-runtime cpython-venv

# Order: --order examples (default) / --order runtimes
# Broader: --all-except-harness
```

**Headless desktop** (dummy SDL — default for matrix/smoke):

```bash
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \
  .venv/bin/python tools/example_test_kit.py --no-unit-tests --only-runtime cpython-venv
```

**Async timers on desktop:** prefer kit `--timer-async` (uses `env_set`, works
for Windows PE under WSL). Shell export of `PYDISPLAY_TIMER_ASYNC=1` also works
on hosts with `getenv`. Semantics: [Runtime — timer_async](../docs/concepts/runtime.md#timer_async-in-srclibboard_configpy).

**Results:** summary on stderr; full JSON defaults to the system temp dir
(`example_test_results.json`), not a path under the repo. Override with
`--results-json PATH`.

**Real X display:** `DISPLAY=:1` (xfce) without dummy SDL opens a window titled
`"<impl> on <platform>"`. Optional: `xvfb-run -a …` (no `SDL_VIDEODRIVER=dummy`)
for a real X11/SDL path without `:1`. Do not require Xvfb in the tools scripts;
wrap when useful. PyScript/Playwright does not need Xvfb.

### Interpreters and binaries

Desktop matrices use repo `.venv` (`cpython-venv`) plus interpreters on
`PATH` / `~/bin` / committed `repo:bin/` (`micropython`, `circuitpython`; see
[`bin/README.md`](../bin/README.md)). `micropython.exe` / `python.exe` are
Windows binaries and cannot run in a Linux cloud sandbox.

After usermod changes that affect these binaries or PyScript vendor wasm, see
[`bin/README.md`](../bin/README.md).

**`micropython.exe` matrix:** no `threading` / `_thread`. The example wrapper
uses a `Runtime.poll` deadline quit (not a multimer SDL quit timer). With
`pydisplay_test_mode.ENABLED`, `Runtime` skips auto-refresh wiring so examples
that call `show()` themselves avoid a competing SDL refresh timer.

### Sibling pure-Python repos

Examples that `import palettes` / `pdwidgets` / `pygraphics` / the ctypes
`usdl2` fallback need those sibling `lib/` dirs on path. The PyPI project
literally named `palettes` is unrelated — do **not** `pip install palettes`.
Prefer TestPyPI native builds for `pygraphics` and `usdl2` when available.

Quick setup: `bash scripts/setup_sibling_repos.sh` (clones current `main`,
writes `.pth` files). The harness auto-discovers the same paths via
`sibling_repos.py`. `pdwidgets` also needs pydisplay's `src/lib` on path
(the harness adds it).

### Known pre-existing failures (not environment bugs)

- `nano_gui_simpletest` needs the matching Hinch `gui/` package.
- `tools/png_test.py` in **pdwidgets** (PNG probe) needs `PDWIDGETS_PNG_DIR` /
  material-design-icons and a sibling pydisplay checkout.

### PyScript matrix

Start or reuse `python tools/serve.py`, then re-run with `--only-runtime pyscript`.
Headless needs Playwright (`.venv/bin/pip install -r requirements-dev.txt` and
`.venv/bin/playwright install chromium`). Without it, pyscript cells report
`needs_playwright` (not a hard failure). Troubleshooting hangs / CDP:
[PyScript — Headless / CDP troubleshooting](../docs/guides/pyscript.md#headless--cdp-troubleshooting).

## LVGL / timer harnesses

| Script | Purpose |
|--------|---------|
| [`run_desktop_lv_tests.py`](run_desktop_lv_tests.py) | LVGL desktop matrix (sync/async, strict clicks) |
| [`lv_timer_test_kit.py`](lv_timer_test_kit.py) | Full LVGL timer matrix (sync/async, all runtimes) |
| [`run_test_timers.py`](run_test_timers.py) | multimer backend probes |
| [`test_timers.py`](test_timers.py) | Host timer probes |

## TestPyPI desktop smoke test

| Script | Purpose |
|--------|---------|
| [`test_testpypi_desktop.sh`](test_testpypi_desktop.sh) | Fresh venv, two-index pip install, `board_config` + SDL draw check |

```bash
./tools/test_testpypi_desktop.sh              # real SDL window
./tools/test_testpypi_desktop.sh --headless   # CI / SSH without DISPLAY
```

Installs `displaysys`, `usdl2`, `pygraphics`, and `lvgl-cpython` (no version pins). See [Publishing micropython-lib — verify after publish](../docs/publishing-micropython-lib.md#4-verify).

| Script | Purpose |
|--------|---------|
| [`test_testpypi_standalone.sh`](test_testpypi_standalone.sh) | Per-package TestPyPI venv import smoke (`multimer`, `displaysys`, `eventsys`, `pygraphics`; `--desktop` adds backend stacks) |

```bash
./tools/test_testpypi_standalone.sh
./tools/test_testpypi_standalone.sh --desktop
```

## Other dev aids

| Script | Purpose |
|--------|---------|
| [`quit_inject.py`](quit_inject.py) | Inject quit into running examples (used by the example harness) |
| [`pydisplay_test_mode.py`](pydisplay_test_mode.py) | Test-mode env for examples |
| [`screenshot.py`](screenshot.py) | Run a desktop example and save its SDL2/pygame-ce window as PNG |
| [`record.py`](record.py) | Run a desktop example and record its SDL2/pygame-ce window with FFmpeg |
| [`typings/`](typings/) | MicroPython stdlib stubs + core package `.pyi` (see below) |

```bash
python tools/screenshot.py hello.py
python tools/screenshot.py bouncing_balls 3
python tools/screenshot.py logo --delay 2 --resolution 320x240 --scale 1
```

Without ``--output``, screenshots are saved as
``docs/screenshots/EXAMPLE_NAME.png``.

```bash
python tools/record.py bouncing_balls
python tools/record.py bouncing_balls 10
python tools/record.py logo --duration 3 --fps 15 --resolution 320x240 --scale 1
```

Without ``--output``, recordings are saved as
``docs/videos/EXAMPLE_NAME.mp4``. Recording requires ``ffmpeg`` on ``PATH`` or
the binary-bundled ``imageio-ffmpeg`` Python package.

### IDE typings (`tools/typings/`)

`stubPath` for Pylance / pyright ([`.vscode/settings.json`](../.vscode/settings.json), [`pyrightconfig.json`](../pyrightconfig.json)):

| Content | Source |
|---------|--------|
| MicroPython stdlib stubs | committed under `tools/typings/` |
| `displaysys` / `eventsys` / `multimer` | committed package trees; regenerate with [`../scripts/gen_package_pyi.sh`](../scripts/gen_package_pyi.sh) |
| `lvgl` | committed `tools/typings/lvgl.pyi` (from `cmods/lv_bindings/generated/lvgl.pyi`) |

Confirm **Python: Select Interpreter** → `.venv/bin/python`. Cursor uses **cursorpyright** with `stubPath` / `typeshedPaths` → `tools/typings` (see [`.vscode/settings.json`](../.vscode/settings.json)).
