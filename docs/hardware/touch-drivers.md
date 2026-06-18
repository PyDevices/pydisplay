# Touch drivers

Touch controller helpers for `board_config.py`.

Source: [`drivers/touch/`](https://github.com/PyDevices/pydisplay/tree/main/drivers/touch)

## board_config.py contract

pydisplay expects the touch section of `board_config.py` to provide:

- `touch_read_func` — callable returning touch coordinates
- `touch_rotation_table` — maps display rotation to touch orientation

See any working board config (e.g. `wokwi_ili9341_ft6x36_esp32s3`) for a complete example.

## Installing drivers

Board packages include the touch driver when needed. Individual install:

```python
mip.install("github:PyDevices/pydisplay/drivers/touch/ft6x36.py", target="./drivers/touch")
```

Micropython-lib index packages: `ft6x36`, `xpt2046`, `cst226`, etc.

## CircuitPython

CircuitPython touch helpers live under `drivers/touch/circuitpython/` (e.g. Adafruit FocalTouch wrapper).
