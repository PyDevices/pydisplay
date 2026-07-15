# Config files

Templates for GUI libraries and ported examples live in [`src/add_ons/`](https://github.com/PyDevices/pydisplay/tree/main/src/add_ons/). Board-specific setup uses [`board_configs/`](https://github.com/PyDevices/pydisplay/tree/main/board_configs) or `src/lib/board_config.py`.

| File | Location | Required for |
|------|----------|--------------|
| `board_config.py` | `board_configs/` or `src/lib/` | **Always** — display, touch, runtime, setup |
| `path.py` | `src/lib/` | Development layout — adds `lib/`, `add_ons/`, `examples/` to path |
| `color_setup.py` | `src/add_ons/` | [Nano-GUI](https://github.com/peterhinch/micropython-nano-gui) — fetch + `ssd` |
| `hardware_setup.py` | `src/add_ons/` | [Micro-GUI](https://github.com/peterhinch/micropython-micro-gui) — fetch + button/encoder `Display` |
| `touch_setup.py` | `src/add_ons/` | [MicroPython-Touch](https://github.com/peterhinch/micropython-touch) — fetch + touch `Display` |
| `fetch_ph_gui.py` | `src/add_ons/` | Installs one of the three `gui/` trees into `add_ons/gui/` |
| `gui/` | `src/add_ons/gui/` | Active Peter Hinch GUI (mip / fetch; not in git) |
| `tft_config.py` | `src/add_ons/` | @russhughes st7789py_mpy examples |

Install add-on templates with [add_ons package](../installation/mip-github.md) or copy files from a full clone.

## board_config.py

Install per-board packages from [board configs](../hardware/board-configs.md) or copy from the closest match.

The default desktop config is `src/lib/board_config.py`.

## path.py

Import before examples when using the `src/` development tree:

```python
import lib.path
```

Not needed if all packages are installed into `/lib` on the device.

## LVGL

Wire pydisplay through upstream [LVGL micropython](https://github.com/lvgl/lv_micropython) using your `board_config.py` display and runtime/touch wiring. See [GUI: LVGL](../guis/lvgl.md) and the [Wokwi project](../guides/wokwi.md) (`wokwi/`).
