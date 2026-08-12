# Config files

Board-specific setup lives in
[`pydevices/board_configs`](https://github.com/PyDevices/pydevices/tree/main/board_configs).
Application and third-party GUI adapters live in pydevices-examples's
[`lib/utils`](https://github.com/PyDevices/pydevices-examples/tree/main/lib/utils).

| File | Location | Purpose |
|---|---|---|
| `board_config.py` | installed from `pydevices/board_configs` | Display, audio, input readers, and timing preference for one board/host |
| `app_runtime.py` | `pydevices-examples/lib/utils` | Optional non-LVGL `eventsys` runtime used by examples |
| `path.py` | `pydevices-examples/lib/utils` | Development-checkout path setup when packages are not installed |
| `color_setup.py` | `pydevices-examples/lib/utils` | Nano-GUI adapter |
| `hardware_setup.py` | `pydevices-examples/lib/utils` | Micro-GUI button/encoder adapter |
| `touch_setup.py` | `pydevices-examples/lib/utils` | MicroPython-Touch adapter |
| `fetch_ph_gui.py` | `pydevices-examples/lib/utils` | Installs one Peter Hinch GUI tree into `utils/gui` |
| `tft_config.py` | `pydevices-examples/lib/utils` | russhughes-style TFT example adapter |

## `board_config.py`

Install a board package using the
[hardware install workflows](https://pydevices.github.io/pydevices/install-workflows.html)
or copy the closest config and customize it. Desktop installs use the
`pydevices-desktop` distribution to provide the default host config.

Board configs instantiate hardware interfaces such as `display_drv`. When
available, they expose neutral capabilities such as `host_read`, `touch_read`,
`keypad_read`, `encoder_read`, `encoder_button_read`, `joystick_driver`,
`emulate`, and `timer_async`. They never instantiate an application runtime.

## Runtime selection

Non-LVGL pydevices-examples applications use:

```python
from app_runtime import runtime
```

An independent application can instantiate the optional coordinator directly:

```python
import board_config
import eventsys

runtime = eventsys.Runtime.from_board_config(board_config)
```

LVGL applications use `from display_driver import runtime`; that coordinator is
part of the LVGL binding and does not use `eventsys`.

## Development checkout paths

Installed packages require no path helper. For a sibling development checkout,
`utils.path` adds pydevices-examples utilities and the canonical pydevices
`lib`, `utils`, and display-driver directories when present:

```python
import utils.path
```

Prefer normal `PYTHONPATH` / `MICROPYPATH` settings when the runtime supports
them. See [Utils](../utils.md#path-setup).
