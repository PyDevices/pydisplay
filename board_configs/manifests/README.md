# Board config manifests

Describe hardware once in TOML; generate MicroPython and CircuitPython
`board_config.py` + `package.json` with:

```bash
.venv/bin/python scripts/generate_board_configs.py
.venv/bin/python scripts/generate_board_configs.py --check   # CI drift gate
.venv/bin/python scripts/generate_board_configs.py --only wokwi_ili9341_ft6x36_esp32s3
```

## Layout

| Path | Purpose |
|------|---------|
| `busdisplay/spi/<slug>.toml` | SPI bus display + optional touch |
| `busdisplay/i80/<slug>.toml` | I80 parallel bus |
| `busdisplay/i2c/<slug>.toml` | I2C OLED |

**26 structured** busdisplay manifests (`busdisplay_spi`, `busdisplay_i2c`, `busdisplay_i80`)
plus **9 verbatim** (complex input/resistive touch). All **18 e-paper** families are
structured. Use `busdisplay_verbatim` only when the generator cannot express the board
(XPT2046 calibration, STMPE610, encoders, joysticks, etc.).

Legacy generators (`generate_cp_board_configs.py`, `generate_epaper_board_configs.py`)
remain for now; new work should extend manifests + `generate_board_configs.py`.

## Schema — busdisplay SPI (`kind = "busdisplay_spi"`)

```toml
kind = "busdisplay_spi"
slug = "wokwi_ili9341_ft6x36_esp32s3"
title = "Human-readable title"
out = "busdisplay/spi"          # under board_configs/

circuitpython = true              # emit cp_<slug> sibling

[display]
module = "ili9341"
class = "ILI9341"
width = 240
height = 320
# optional chip kwargs: colstart, rowstart, rotation, bgr, invert, ...

[display.cp]                      # optional CP-only kwargs; width/height fall back from [display]
colstart = 0
rowstart = 0
rotation = 0
mirrored = false
color_depth = 16
bgr = true
reverse_bytes_in_word = true
invert = false

[bus.mp.spi]
id = 1
baudrate = 60_000_000
sck = 36
mosi = 35
miso = 37
dc = 16
cs = 5

[touch]
module = "ft6x36"
class = "FT6x36"
read = "get_positions"            # attribute on touch_drv
rotation_table = [6, 3, 0, 5]

[touch.mp.i2c]
id = 0
sda = 7
scl = 6
freq = 100_000

[package]
display_driver = "ili9341"
touch_driver = "ft6x36"
deps_mp = ["spibus"]
```

Omit `[touch]` for display-only boards (`runtime = None`).

## Schema — epaper (`epaperdisplay.toml`)

Each `[[board]]` row describes one e-paper CP+MP pair. Optional nested tables:

- `[board.cp]` — CP-only chip kwargs (e.g. `ram_offset = 1`)
- `[board.mp_bus]` / `[board.cp_bus]` — non-default SPI / FourWire pinout
- `template = "magtag"` — MagTag keypad + custom EPD wiring
- `class = "ACeP7In"` when module name differs from driver class
