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

## LVGL / timer harnesses

| Script | Purpose |
|--------|---------|
| [`run_desktop_lv_tests.py`](run_desktop_lv_tests.py) | LVGL desktop executable matrix |
| [`lv_timer_test_kit.py`](lv_timer_test_kit.py) | Smaller LVGL timer matrix |
| [`run_test_timers.py`](run_test_timers.py) | multimer backend probes |
| [`test_timers.py`](test_timers.py) | Host timer probes |

## Other dev aids

| Script | Purpose |
|--------|---------|
| [`run_display_teardown_tests.py`](run_display_teardown_tests.py) | Display backend teardown checks |
| [`test_keypad_*_sim.py`](test_keypad_click_sim.py) | Keypad simulation |
| [`quit_inject.py`](quit_inject.py) | Inject quit into running examples |
| [`pydisplay_test_mode.py`](pydisplay_test_mode.py) | Test-mode env for examples |
| [`typings/`](typings/) | MicroPython type stubs (see `.vscode/settings.json`) |
