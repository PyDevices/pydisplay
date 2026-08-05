# Config files

Templates for GUI libraries and ported examples live in [`src/utils/`](https://github.com/PyDevices/pydisplay/tree/main/src/utils/). Board-specific setup uses [`micropython-hardware` `board_configs/`](https://github.com/PyDevices/micropython-hardware/tree/main/board_configs) or `src/lib/board_config.py`.

| File | Location | Required for |
|------|----------|--------------|
| `board_config.py` | micropython-hardware `board_configs/` or `src/lib/` | **Always** — display, touch, runtime, setup |
| `path.py` | `src/utils/` | Optional — adds `lib/`, `utils/`, and cwd to path when `PYTHONPATH`/`MICROPYPATH` isn't set |
| `color_setup.py` | `src/utils/` | [Nano-GUI](https://github.com/peterhinch/micropython-nano-gui) — fetch + `ssd` |
| `hardware_setup.py` | `src/utils/` | [Micro-GUI](https://github.com/peterhinch/micropython-micro-gui) — fetch + button/encoder `Display` |
| `touch_setup.py` | `src/utils/` | [MicroPython-Touch](https://github.com/peterhinch/micropython-touch) — fetch + touch `Display` |
| `fetch_ph_gui.py` | `src/utils/` | Installs one of the three `gui/` trees into `utils/gui/` |
| `gui/` | `src/utils/gui/` | Active Peter Hinch GUI (mip / fetch; not in git) |
| `tft_config.py` | `src/utils/` | @russhughes st7789py_mpy examples |

Install add-on templates with [utils package](../installation/mip-github.md) or copy files from a full clone.

## board_config.py

Install per-board packages from [board configs](https://pydevices.github.io/micropython-hardware/board-configs.html) or copy from the closest match.

The default desktop config is `src/lib/board_config.py`.

## path.py

Preferred on desktop: set `PYTHONPATH` (CPython/CircuitPython) or `MICROPYPATH` (MicroPython) to `.:lib:utils` and `cd src` before running — no import needed.

When environment variables are unavailable or not set as recommended, follow [Utils path setup](../utils.md#path-setup) and [README path environment forms](../../README.md#321-path-environment-forms). The fallback import is:

```python
import utils.path  # see ../utils.md#path-setup
```

Not needed if all packages are installed into `/lib` on the device.

## LVGL

Wire pydisplay through upstream [LVGL micropython](https://github.com/lvgl/lv_micropython) using your `board_config.py` display and runtime/touch wiring. See [GUI: LVGL](../guis/lvgl.md) and the [Wokwi project](../guides/wokwi.md) (`wokwi/`).
