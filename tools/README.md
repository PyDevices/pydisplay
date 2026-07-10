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
# http://127.0.0.1:8000/web/pyscript/load.html?modules=calculator

./tools/pyscript.sh calculator
./tools/jupyter.sh calculator --cursor
```

See [Run the notebook interactively](../docs/platforms/jupyter-run.md) and [PyScript local development](../docs/guides/pyscript.md).

## PyScript headless debug (Playwright)

| Script | Purpose |
|--------|---------|
| [`ps_debug.py`](ps_debug.py) | CDP console + network probe for an embed/load URL |
| [`ps_screenshot.py`](ps_screenshot.py) | Timed screenshot; console via CDP (avoids `evaluate` during WASM sleep) |
| [`ps_shot.py`](ps_shot.py) | Screenshot with a hard kill if Chromium stalls |

Agent-oriented guide: [PyScript troubleshooting](../docs/testing/pyscript-troubleshooting.md).

```bash
python tools/serve.py   # separate terminal
.venv/bin/python tools/ps_debug.py \
  'http://127.0.0.1:8000/web/pyscript/embed.html?modules=calculator&autotest=1' 20
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

## MicroPython framebuf parity

| Script | Purpose |
|--------|---------|
| [`compare_framebuf_mp.py`](compare_framebuf_mp.py) | Compare built-in C ``framebuf`` vs ``src/add_ons/framebuf.py`` on-device |
| [`compare_graphics_mp.py`](compare_graphics_mp.py) | Compare native ``graphics`` cmod vs ``src/lib/graphics`` on-device |
| [`sync_framebuf.py`](sync_framebuf.py) | Copy canonical ``add_ons/framebuf.py`` → ``lib/graphics/framebuf.py`` |

```bash
micropython tools/compare_framebuf_mp.py
micropython tools/compare_graphics_mp.py
micropython.exe tools/compare_framebuf_mp.py
```

Exit 0 when buffers and constants match; prints each check and exits 1 on mismatch.

## LVGL / timer harnesses

| Script | Purpose |
|--------|---------|
| [`run_desktop_lv_tests.py`](run_desktop_lv_tests.py) | LVGL desktop matrix (pump/async, strict clicks) |
| [`lv_timer_test_kit.py`](lv_timer_test_kit.py) | Full LVGL timer matrix (no_pump/pump/async, all runtimes) |
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

Installs `displaysys-sdldisplay`, `graphics-cmod`, and `lvgl-cpython` (no version pins). See [Publishing micropython-lib — verify after publish](../docs/publishing-micropython-lib.md#4-verify).

| Script | Purpose |
|--------|---------|
| [`test_testpypi_standalone.sh`](test_testpypi_standalone.sh) | Per-package TestPyPI venv import smoke (`multimer`, `displaysys`, `eventsys`, `pydisplay-graphics`; `--desktop` adds backend stacks) |

```bash
./tools/test_testpypi_standalone.sh
./tools/test_testpypi_standalone.sh --desktop
```

## Other dev aids

| Script | Purpose |
|--------|---------|
| [`run_display_teardown_tests.py`](run_display_teardown_tests.py) | Display backend teardown checks |
| [`test_keypad_*_sim.py`](test_keypad_click_sim.py) | Keypad simulation |
| [`quit_inject.py`](quit_inject.py) | Inject quit into running examples |
| [`pydisplay_test_mode.py`](pydisplay_test_mode.py) | Test-mode env for examples |
| [`typings/`](typings/) | MicroPython + LVGL type stubs (see below) |

### IDE typings (`tools/typings/`)

Pylance needs stubs for the installed `lvgl-cpython` binary (`.so` has no Python source).

| File | Purpose |
|------|---------|
| [`.vscode/settings.json`](../.vscode/settings.json) | `python.analysis.stubPath`, `extraPaths`, Pylance |
| [`pyrightconfig.json`](../pyrightconfig.json) | Shared stub/extraPaths (also read by Pylance) |
| [`typings/lvgl/__init__.pyi`](typings/lvgl/__init__.pyi) | Symlink → `../lvgl.pyi` (Pylance package layout) |

After `pip install` / reinstall of `lvgl-cpython`, refresh the venv symlink:

```bash
./tools/link_lvgl_stubs.sh
```

Then **Reload Window** and confirm **Python: Select Interpreter** → `.venv/bin/python`.

Use the **Pylance** language server (`.vscode/settings.json` sets `"python.languageServer": "Pylance"`). Disable or uninstall the **BasedPyright** extension if installed — it conflicts with Pylance. Remove any `"python.languageServer": "None"` from user settings.

**Go to Definition** on `import lvgl` should open `tools/typings/lvgl.pyi`. If not, check **Output → Pylance** for stub-path warnings.
