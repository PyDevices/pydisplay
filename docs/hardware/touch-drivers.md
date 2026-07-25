# Touch drivers

Touch controller helpers for `board_config.py`.

Source: [`drivers/touch/`](https://github.com/PyDevices/pydisplay/tree/main/drivers/touch)

## board_config.py contract

Target wiring (see [Board devices — touch duck-type](board-devices.md#touch-duck-type)):

- `touch` — driver object with `read_points()` → `()` when up, else a sequence of
  `(x, y[, id[, …]])`
- `runtime = eventsys.Runtime(..., touch_read=touch.read_points, …)`
- optional `touch_rotation_table` — maps display rotation to touch orientation

Apps use `runtime.touch_dev` (and `.points` for multipoint), not the raw driver.
Do not collapse multi-touch to `points[0]` in the board file — return the full
`read_points()` sequence (or a sequence-preserving map).

See any working board config (e.g. `wokwi_ili9341_ft6x36_esp32s3` or
`fbdisplay/esp32-p4-wifi6-touch-lcd-4b`) for a complete example.

## Installing drivers

Board packages include the touch driver when needed. Individual install:

```python
mip.install("github:PyDevices/pydisplay/packages/tt21100.json", target="./")
mip.install("github:PyDevices/pydisplay/packages/stmpe610.json", target="./")
mip.install("github:PyDevices/micropython-hardware/drivers/touch/ft6x36.py", target="./drivers/touch")
```

Micropython-lib index packages: `ft6x36`, `xpt2046`, `cst226`, `tt21100`, `stmpe610`, etc.

## MicroPython drivers

| File | Chip | Typical boards |
|------|------|----------------|
| `ft6x36.py` | FocalTech FT6x36 | ESP32-S3 dev boards, Wokwi |
| `tt21100.py` | TT21100 | PyPortal, FunHouse |
| `stmpe610.py` | STMPE610 | PiTFT FeatherWing |
| `xpt2046.py` | XPT2046 | Resistive SPI touch |
| `gt911.py` | GT911 | Many ESP32 panels |
| `cst8xx.py` | CST816/CST820 | Capacitive I2C |
| `cst226.py` | CST226 | Capacitive I2C |
| `chsc6x.py` | CHSC6x | Capacitive I2C |

## CircuitPython shims

Adafruit touch libraries vendored under `drivers/touch/circuitpython/`:

| File | Chip |
|------|------|
| `adafruit_focaltouch.py` | FocalTech FT6x36 family |
| `adafruit_ft5336.py` | FT5336 |
| `adafruit_tsc2007.py` | TSC2007 resistive |
| `adafruit_tt21100.py` | TT21100 (PyPortal) |
| `adafruit_stmpe610.py` | STMPE610 (PiTFT) |
| `adafruit_touchscreen.py` | 4-wire analog resistive |

See [driver inventory](driver-inventory.md) for the full list.

## Calibration (STMPE610 / PiTFT)

PiTFT FeatherWing configs pass Adafruit's factory calibration for the 2.4" wing
(rotation 90°):

```python
_PITFT_CALIBRATION = ((357, 3812), (390, 3555))
```

MicroPython (`pitft_ili9341_featherwing`) passes this to `STMPE610(..., calibration=...)`.
CircuitPython (`cp_pitft_ili9341_featherwing`) passes the same tuple to
`Adafruit_STMPE610_SPI`.
