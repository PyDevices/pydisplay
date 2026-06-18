# Wokwi

Try pydisplay in the browser simulator without hardware.

## In-repo projects

Runnable projects live under [`wokwi/`](https://github.com/PyDevices/pydisplay/tree/main/wokwi):

| Directory | Description |
|-----------|-------------|
| [`wokwi/minimum/`](https://github.com/PyDevices/pydisplay/tree/main/wokwi/minimum) | Core packages + Wokwi board config + `hello.py` |
| [`wokwi/esp32-s3-full/`](https://github.com/PyDevices/pydisplay/tree/main/wokwi/esp32-s3-full) | Full install (bundle, add_ons, examples) via `installer.py` |

Each folder contains `main.py`, `diagram.json`, and `wokwi.toml`. See [`wokwi/README.md`](https://github.com/PyDevices/pydisplay/blob/main/wokwi/README.md) for setup on [wokwi.com](https://wokwi.com) and VS Code.

**Quick start (browser):** create a [new ESP32-S3 MicroPython project](https://wokwi.com/projects/new/micro-python-esp32-s3), paste in `wokwi/minimum/main.py` and `diagram.json`, and run.

## Hosted projects (legacy)

These predate the in-repo projects; behavior should match `wokwi/minimum/` and `wokwi/esp32-s3-full/`:

| Project | Description |
|---------|-------------|
| [415770470006384641](https://wokwi.com/projects/415770470006384641) | Full PyDisplay ESP32-S3 example — uses `installer.py` |
| [404248867674669057](https://wokwi.com/projects/404248867674669057) | Minimum configuration (displaysys + eventsys + board config) |

## In-repo board configs

Wiring matches these MIP packages:

| Config | Touch |
|--------|-------|
| `board_configs/busdisplay/spi/wokwi_ili9341_ft6x36_esp32s3` | FT6X36 |
| `board_configs/busdisplay/spi/wokwi_ili9341_esp32s3_no_touch` | None |

```python
import mip
mip.install("github:PyDevices/pydisplay/board_configs/busdisplay/spi/wokwi_ili9341_ft6x36_esp32s3")
```

## installer.py on Wokwi

The full example downloads and runs [`installer.py`](../installation/installer.md). The in-repo [`wokwi/esp32-s3-full/main.py`](https://github.com/PyDevices/pydisplay/blob/main/wokwi/esp32-s3-full/main.py) does the same with the Wokwi board config.

## Known issues

`touch_keypad.py` notes occasional Wokwi `IndexError` when touching the last keypad row — simulator quirk, not necessarily hardware.
