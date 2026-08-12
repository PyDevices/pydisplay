# pydevices-examples `tools/`

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

### Preferred method (parallel runtimes, fail-fast, both timer modes)

For thorough verification (timer/multimer/runtime changes, or “run the full
matrix”), prefer **example-by-example**, **all selected runtimes in parallel**
per example (`--jobs 0`, default), **`--fail-fast`**, and **both**
`PYDEVICES_TIMER_ASYNC` modes as separate kit runs.

| Mode | Runtimes |
|------|----------|
| Sync (`PYDEVICES_TIMER_ASYNC=0`) | **5** desktop SDL: `micropython`, `micropython.exe`, `circuitpython`, `cpython-venv`, `python.exe` |
| Async (`PYDEVICES_TIMER_ASYNC=1`) | **7** — the five above plus `pyscript`, `jupyter` |
| Android (opt-in) | `android` — `pydevices-android-template/scripts/android.sh` (or `~/bin/android.sh`) + emulator/device + `org.pydevices.launcher` APK; **not** in the default 5/7 lists (`--only-runtime android`) |

Default timing is already short (`duration_s=2`, `timeout_s=15` in the
runtimes/manifest defaults). After each example’s parallel wave finishes, if
any cell failed, stop before the next example; fix the root cause, then resume.

```bash
# PyScript needs the static server (async mode)
python tools/serve.py   # separate terminal; reuse if already on :8000

export SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy PYTHONUNBUFFERED=1
mkdir -p /tmp/pydevices-examples-matrix

SYNC_RT="micropython micropython.exe circuitpython cpython-venv python.exe"
ASYNC_RT="$SYNC_RT pyscript jupyter"

set -o pipefail   # keep kit exit status through tee

# Sync — 5 runtimes concurrently per example
PYDEVICES_TIMER_ASYNC=0 stdbuf -oL -eL \
  .venv/bin/python tools/example_test_kit.py --no-unit-tests --fail-fast \
  --only-runtime $SYNC_RT \
  --results-json /tmp/pydevices-examples-matrix/sync.json \
  2>&1 | stdbuf -oL -eL tee /tmp/pydevices-examples-matrix/sync.log

# After sync is clean — async, all 7
PYDEVICES_TIMER_ASYNC=1 stdbuf -oL -eL \
  .venv/bin/python tools/example_test_kit.py --no-unit-tests --fail-fast \
  --only-runtime $ASYNC_RT \
  --results-json /tmp/pydevices-examples-matrix/async.json \
  2>&1 | stdbuf -oL -eL tee /tmp/pydevices-examples-matrix/async.log
```

Live log lines: `Running <example> @ N runtime(s) in parallel...`, then
`start` / `done` per runtime. `--fail-fast` waits for the current example’s
workers, then exits if any cell failed. Resume with `--only-example`
(remaining ids) or by restarting that mode from the failed example. Use
`--jobs 1` for fully serial runtimes when isolating races. See
[Windows PE under WSL](#windows-pe-under-wsl) for PE window / quit notes.

`--curated-only` is a smoke shortcut, not a substitute for the preferred gate.

### Matrix commands (scoped / smoke)

```bash
# Curated set across available runtimes (smoke)
.venv/bin/python tools/example_test_kit.py --curated-only

# Scope (space-separated ids on one flag; see note below)
.venv/bin/python tools/example_test_kit.py --only-example calculator --only-runtime micropython
.venv/bin/python tools/example_test_kit.py --no-unit-tests --only-runtime cpython-venv micropython
.venv/bin/python tools/example_test_kit.py --no-unit-tests \
  --only-example calc_lvgl lv_test_timer --only-runtime circuitpython

# Order: --order examples (default) / --order runtimes
# Broader: --all-except-harness
```

`--only-example` and `--only-runtime` use `nargs="+"`: pass multiple ids
space-separated after **one** occurrence of the flag. Repeating the flag
silently keeps only the last list (`--only-runtime circuitpython --only-runtime
python.exe` runs just `python.exe`). Same rule for `lv_timer_test_kit.py`
`--only` / `--modes`.

**Headless desktop** (dummy SDL — default for matrix/smoke):

```bash
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \
  .venv/bin/python tools/example_test_kit.py --no-unit-tests --only-runtime cpython-venv
```

Unix subprocesses see that shell export. Windows `.exe` behavior is different —
see [Windows PE under WSL](#windows-pe-under-wsl).

**Async timers on desktop:** the kit forwards `PYDEVICES_TIMER_ASYNC` as wrapper
`--timer-async` (uses `env_set`, works for Windows PE under WSL). Shell export
is the preferred way to select mode for a full kit run (see Preferred method
above). Semantics: [Runtime — timer_async](https://pydevices.github.io/pydevices/application-runtime.html#timer_async-in-srclibboard_configpy).

### Windows PE under WSL

`micropython.exe` and `python.exe` are Windows PE binaries launched from WSL.
They cannot read Linux-exported environment variables. The kit therefore
forwards only values that must cross that boundary via wrapper argv +
`displaydev.env_set` (notably `--timer-async` / `--multimer-backend`).

**Do not forward `SDL_VIDEODRIVER` / `SDL_AUDIODRIVER` to PE.** Unix cells stay
headless from the shell `SDL_*=dummy` export; PE keeps a real Windows video
driver. During a matrix run you should see `micropython.exe` / `python.exe`
windows — that means the cell started and is usable. Forwarding `dummy` into
PE hides those windows.

**`summary: hang` on PE is usually a quit failure, not a dead process.** If the
Windows window stays up past `duration_s` / until the kit `timeout_s`, the
example is still running (you can interact with it); the harness timed out
waiting for cooperative quit / `EXAMPLE_RESULT`. PE child output is captured
via temp files so a timeout kill does not wipe stdout the way pipes often did.
Fix the quit path (wrapper deadline / `pydevices_test_mode` / inject) rather
than treating PE as “failed to launch.”

**Scheduling:** with `--order examples` and `--jobs 0` (default), **all**
selected runtimes for an example — including both `.exe` launchers — run
concurrently.

**Results:** live `Running <example> @ <runtime>...` lines on stderr; summary
table at end (or when `--fail-fast` stops). Full JSON defaults to the system
temp dir (`example_test_results.json`), not a path under the repo. Override
with `--results-json PATH`.

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
`pydevices_test_mode.ENABLED`, `Runtime` skips auto-refresh wiring so examples
that call `show()` themselves avoid a competing SDL refresh timer. WSL PE
scheduling and SDL env rules:
[Windows PE under WSL](#windows-pe-under-wsl).

### Sibling pure-Python repos

Examples that `import palettes` / `pdwidgets` / `pygraphics` / the ctypes
`usdl2` fallback need those sibling `lib/` dirs on path. The PyPI project
literally named `palettes` is unrelated — do **not** `pip install palettes`.
Prefer TestPyPI native builds for `pygraphics` and `usdl2` when available.

Quick setup: `bash scripts/setup_sibling_repos.sh` (clones current `main`,
writes `.pth` files). The harness auto-discovers the same paths via
`sibling_repos.py`. `pdwidgets` also needs pydevices's `lib` on path
(the harness adds it).

### Known pre-existing failures (not environment bugs)

- `nano_gui_simpletest` needs the matching Hinch `gui/` package.
- `tools/png_test.py` in **pdwidgets** (PNG probe) needs `PDWIDGETS_PNG_DIR` /
  material-design-icons and a sibling pydevices-examples checkout.

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
| [`multimer_backend_preload.py`](multimer_backend_preload.py) | Force one multimer backend, then run a script |

**Comparing multimer backends:** `lv_timer_test_kit.py --backend NAME` (or
`example_test_kit.py` with `MULTIMER_BACKEND` set, which forwards
`--multimer-backend` to the wrapper). Both call `multimer.use_backend()` inside
the child, so they also work for the Windows `.exe` runtimes, which cannot read
WSL-exported env vars. Runtimes lacking that backend report `unavailable` and do
not fail the run. Semantics: [multimer — Overriding the backend](https://pydevices.github.io/pydevices/multimer.html#overriding-the-backend).

## TestPyPI desktop smoke test

| Script | Purpose |
|--------|---------|
| [`test_testpypi_desktop.sh`](test_testpypi_desktop.sh) | Fresh venv, two-index pip install, `board_config` + SDL draw check |

```bash
./tools/test_testpypi_desktop.sh              # real SDL window
./tools/test_testpypi_desktop.sh --headless   # CI / SSH without DISPLAY
```

Installs `displaydev`, `usdl2`, `pygraphics`, and `pydevices-lvgl` (no version pins). See the [product publishing guide](https://pydevices.github.io/pydevices/publishing.html).

| Script | Purpose |
|--------|---------|
| [`test_testpypi_standalone.sh`](test_testpypi_standalone.sh) | Per-package TestPyPI venv import smoke (`multimer`, `displaydev`, `eventsys`, `pygraphics`; `--desktop` adds backend stacks) |

```bash
./tools/test_testpypi_standalone.sh
./tools/test_testpypi_standalone.sh --desktop
```

## Other dev aids

| Script | Purpose |
|--------|---------|
| [`quit_inject.py`](quit_inject.py) | Inject quit into running examples (used by the example harness) |
| [`pydevices_test_mode.py`](pydevices_test_mode.py) | Test-mode env for examples |
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

`stubPath` for Pylance / pyright (`.vscode/settings.json`, [`pyrightconfig.json`](../pyrightconfig.json)):

| Content | Source |
|---------|--------|
| MicroPython stdlib stubs | committed under `tools/typings/` |
| `displaydev` / `eventsys` / `multimer` / `events` / `keys` | committed package trees / modules; regenerate with [`../scripts/gen_package_pyi.sh`](../scripts/gen_package_pyi.sh) |
| `lvgl` | committed `tools/typings/lvgl.pyi` (from `cmods/lvgl-bindings/generated/lvgl.pyi`) |

Confirm **Python: Select Interpreter** → `.venv/bin/python`. Cursor uses **cursorpyright** with `stubPath` / `typeshedPaths` → `tools/typings` (configured in a local `.vscode/settings.json` when present).
