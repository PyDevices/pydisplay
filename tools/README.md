# pydisplay `tools/`

Developer workflow only — local servers, test harnesses, and IDE typings. For repo maintenance see [`scripts/README.md`](../scripts/README.md).

## PyScript / Jupyter launchers

| Script | Purpose |
|--------|---------|
| [`serve.py`](serve.py) | HTTP server with Cross-Origin-Isolation headers |
| [`pyscript.sh`](pyscript.sh) | Open one example in the browser — `./tools/pyscript.sh calculator` |
| [`jupyter.sh`](jupyter.sh) | JupyterLab or Cursor notebooks — `./tools/jupyter.sh calculator` |

From repo root:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt   # playwright, pytest (optional)
.venv/bin/playwright install chromium           # headless PyScript matrix

python tools/serve.py
# http://127.0.0.1:8000/web/pyscript/index.html
# http://127.0.0.1:8000/web/pyscript/micropython.html?modules=calc_graphics,calc_engine

./tools/pyscript.sh calculator
./tools/jupyter.sh calculator --cursor
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

Agent-oriented guide: [PyScript troubleshooting](../.cursor/pyscript-troubleshooting.md).

```bash
python tools/serve.py   # separate terminal
.venv/bin/python tools/ps_debug.py \
  'http://127.0.0.1:8000/web/pyscript/harness.html?modules=calc_graphics,calc_engine&autotest=1' 20
```

## Example test matrix

| Script | Purpose |
|--------|---------|
| [`example_test_kit.py`](example_test_kit.py) | Cross-runtime example matrix |
| [`example_test_manifest.toml`](example_test_manifest.toml) | Per-example metadata |
| [`example_runtimes.toml`](example_runtimes.toml) | Runtime command templates |

```bash
python tools/example_test_kit.py --curated-only
python tools/example_test_kit.py --only-example calculator --only-runtime micropython
```

Headless desktop default is `SDL_VIDEODRIVER=dummy` (see `AGENTS.md`). For a real
X11/SDL window without a logged-in display, agents may wrap with `xvfb-run -a`
— details in [AGENTS.md — Running examples headlessly](../AGENTS.md#running-examples-headlessly-gui-smoke-tests).

## Graphics / framebuf parity

| Script | Purpose |
|--------|---------|
| [`compare_framebuf_mp.py`](compare_framebuf_mp.py) | Compare built-in C ``framebuf`` vs ``src/add_ons/framebuf.py`` on-device |
| [`compare_graphics.py`](compare_graphics.py) | Shared compare engine (native ``pygraphics`` cmod vs staged pure-Python ``pygraphics``) |
| [`compare_graphics_run.py`](compare_graphics_run.py) | Single-runtime subprocess entry (prints ``GRAPHICS_COMPARE_RESULT=`` JSON) |
| [`compare_graphics_matrix.py`](compare_graphics_matrix.py) | Cross-runtime matrix (MP, CP, CPython; installs ``pygraphics-cmod`` from TestPyPI for CPython) |

```bash
# One runtime
micropython tools/compare_graphics_run.py

# Full desktop matrix (from repo root)
python tools/compare_graphics_matrix.py
python tools/compare_graphics_matrix.py --only-runtime micropython,cpython-venv
```

Expanded coverage includes ``FrameBuffer`` shape ops, module-level helpers, ``Draw`` (clip, text8), and per-glyph font probes (ASCII 32–126) to catch romfont mapping bugs in ``pygraphics-cmod``.

Results JSON: ``.cursor/compare_graphics_results.json``. Exit 0 when all runtimes pass; exit 1 on any mismatch or setup failure.

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

Installs `displaysys`, `usdl2`, `pygraphics-cmod`, and `lvgl-cpython` (no version pins). See [Publishing micropython-lib — verify after publish](../docs/publishing-micropython-lib.md#4-verify).

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
| `lvgl` | **`lvgl-cpython`** installs `lvgl.pyi` next to the extension — not in-tree |

Confirm **Python: Select Interpreter** → `.venv/bin/python`. Use **Pylance** (disable BasedPyright if it conflicts).
