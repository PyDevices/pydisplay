# Config files

Templates and examples live in [`src/configs/`](https://github.com/PyDevices/pydisplay/tree/main/src/configs) and board-specific trees.

| File | Required for |
|------|--------------|
| `board_config.py` | **Always** — display, touch, brokers, setup |
| `path.py` | Development layout — adds `lib/`, `examples/` to path |
| `color_setup.py` | [Nano-GUI](https://github.com/peterhinch/micropython-nano-gui) |
| `hardware_setup.py` | [MicroPython-Touch](https://github.com/peterhinch/micropython-touch) |
| `lv_config.py` | [LVGL](https://github.com/lvgl/lv_micropython) — create/adapt for your board |
| `tft_config.py` | @russhughes st7789py_mpy examples |

## board_config.py

Install per-board packages from [board configs](../hardware/board-configs.md) or copy from the closest match.

The default desktop config is `src/lib/board_config.py`.

## path.py

Import before examples when using the `src/` development tree:

```python
import lib.path
```

Not needed if all packages are installed into `/lib` on the device.

## LVGL note

There is no checked-in `src/examples/lv_config.py` yet. For LVGL, follow [LVGL micropython](https://github.com/lvgl/lv_micropython) documentation and wire displaysys as the display driver — see [GUI: LVGL](../guis/lvgl.md).
