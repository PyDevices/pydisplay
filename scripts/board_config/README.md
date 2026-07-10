# Board config generator source

Manifest TOMLs and hand-maintained exceptions live here. **`board_configs/` is output only**
— each board directory contains just `board_config.py` and optionally `package.json`.

Describe hardware once in TOML; generate MicroPython and CircuitPython
`board_config.py` + `package.json` with:

```bash
.venv/bin/python scripts/generate_board_configs.py
.venv/bin/python scripts/generate_board_configs.py --check   # CI drift gate
.venv/bin/python scripts/generate_board_configs.py --only wokwi_ili9341_ft6x36_esp32s3
.venv/bin/python scripts/generate_board_configs.py --hand-maintained-only
```

## Regenerate full tree

```bash
rm -rf board_configs
.venv/bin/python scripts/generate_board_configs.py
.venv/bin/python scripts/generate_board_configs.py --check
```

`--check` also fails if any file under `board_configs/` is not `board_config.py` or
`package.json` (no manifests, `boot1.py`, or `__pycache__` left behind).

## Source layout

| Path | Purpose |
|------|---------|
| `manifests/busdisplay/spi/<slug>.toml` | SPI bus display + optional touch |
| `manifests/busdisplay/i80/<slug>.toml` | I80 parallel bus |
| `manifests/busdisplay/i2c/<slug>.toml` | I2C OLED |
| `hand_maintained/` | Non-manifest boards copied verbatim to `board_configs/` |

**Hand-maintained exceptions** (not driven by manifests):

- `hand_maintained/fbdisplay/cp_usb_video/` — CircuitPython USB Video (CP-only; no `package.json`)
- `hand_maintained/jndisplay/`, `pgdisplay/`, `psdisplay/`, `sdldisplay/` — host desktop backends

## Manifest kinds

**34 structured** busdisplay manifests (`busdisplay_spi`, `busdisplay_i2c`, `busdisplay_i80`).
**2 structured** fbdisplay manifests (`fbdisplay_mipidsi`). **13 more** fbdisplay boards use
``fbdisplay_picodvi``, ``fbdisplay_rgbmatrix``, or ``fbdisplay_rgbframebuffer``.
All **18 e-paper** families are in `manifests/epaperdisplay.toml` (generate with
`scripts/generate_board_configs.py`, or `--kind epaper` to limit). **2 pixeldisplay**
manifests (`pixeldisplay` — NeoPixel / DotStar grids). Use `mp_preamble` for
board-specific setup lines (e.g. shared reset GPIO on WT32-SC01 Plus).

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

### Alternate input (`[input.*]`)

MicroPython-only sections wire `runtime.add_encoder`, `add_keypad`, or
`add_joystick` after display setup. CircuitPython siblings may use
`[input.keypad_gpio]` (PyBadge-style GPIO buttons).

```toml
[input.encoder]
module = "rotary_irq_esp"
class = "RotaryIRQ"
pin_a = 1
pin_b = 2
pull_up = true
half_step = true
button_pin = 0

[input.keypad_shift]
clock = 63
latch = 32
data = 62
mapping = "PYBADGE_BUTTON_MAP"

[input.joystick]
module = "gpiojoystick"
class = "GPIOJoystick"
instance_id = 1
axes = [{ pin = 39, atten = "ADC.ATTN_11DB" }]
buttons = [4, 25, 26]
emulate_digital = [[0, 1]]
```

### Resistive touch (`[touch]` with `type = "xpt2046"` or `"stmpe610"`)

XPT2046 uses a separate SPI bus plus optional `[touch.calibrate]`. STMPE610
uses shared SPI pins and `[touch.calibration]` / `read_wrapper = "stmpe610"`.

```toml
[touch]
type = "xpt2046"
module = "xpt2046"
class = "Touch"
read = "get_touch"
rotation_table = [0, 0, 0, 4]

[touch.mp.spi]
id = 2
baudrate = 1_000_000
sck = 18
mosi = 23
miso = 19
cs = 25
int_pin = 21

[touch.calibrate]
xmin = 107
xmax = 2000
ymin = 200
ymax = 1940
width = "display_drv.height"
height = "display_drv.width"
orientation = 3

[touch.cp]
pins = ["board.D25", "board.D26", "board.D27", "board.D32"]
x_resistance = 400
```

## Schema — fbdisplay MIPI DSI (`kind = "fbdisplay_mipidsi"`)

Targets the displayif ``mipidsi`` cmod (MicroPython) and CircuitPython
``mipidsi``.  Wrap the native framebuffer with ``FBDisplay(fb)``.

```toml
kind = "fbdisplay_mipidsi"
slug = "esp32-p4-wifi6-touch-lcd-4b"
out = "fbdisplay"
port = "esp32p4"                  # esp32p4 | mimxrt1176
circuitpython = true
mp_lcd_reset_pulse = true
cp_lcd_reset_pulse = true
cp_framebuffer_display = true     # CP: FramebufferDisplay(fb, auto_refresh=True)

[bus]
frequency = 1_000_000_000
num_lanes = 2
ldo_chan = 3                      # ESP32-P4 only
ldo_voltage_mv = 2500

[display]
init_sequence_name = "ST7703_INIT_SEQUENCE"
init_sequence_hex = ["b903f11283"]  # or init_sequence_empty = true
width = 720
height = 720
pixel_clock_frequency = 38_000_000
reset_pin = "LCD_RESET"
backlight_pin = "LCD_BACKLIGHT"

[touch.chip]
reset_pin = "TOUCH_RESET"
address = "0x5D"

[package]
touch_driver = "gt911"
include_mipidsi = true
```

## Schema — fbdisplay picodvi (`kind = "fbdisplay_picodvi"`)

displayif ``picodvi.Framebuffer`` on RP2040 (PIO) or RP2350 (HSTX). ``refresh()``
is a no-op; scanout is continuous.

```toml
kind = "fbdisplay_picodvi"
slug = "pimoroni_pico_dv_base_640x480"
port = "rp2040"                   # rp2040 | rp2350
circuitpython = true

[fb]
width = 640
height = 480
color_depth = 8

[pins.mp]
clk_dp = 7
clk_dn = 6
# red/green/blue _dp/_dn pairs ...

[pins.cp]
clk_dp = "board.CKP"
clk_dn = "board.CKN"
```

## Schema — fbdisplay rgbmatrix (`kind = "fbdisplay_rgbmatrix"`)

displayif ``rgbmatrix.RGBMatrix`` (HUB75 / Protomatter). Wrap with
``FBDisplay(matrix, width=…, height=…)``.

```toml
kind = "fbdisplay_rgbmatrix"
slug = "matrixportal_s3_64x64"
circuitpython = true
cp_matrix_alias = true            # CP: fb = matrix before FBDisplay

[matrix]
width = 64
height = 64
bit_depth = 4
rgb_pins = [42, 41, 40, 38, 39, 37]
addr_pins = [45, 36, 48, 35, 21]
clock_pin = 2
latch_pin = 47
output_enable_pin = 14
doublebuffer = true

[matrix.cp]
rgb_pins = ["board.MTX_R1", "board.MTX_G1", ...]
```

## Schema — fbdisplay rgbframebuffer (`kind = "fbdisplay_rgbframebuffer"`)

displayif ``rgbframebuffer.RGBFrameBuffer`` (ESP32 RGB LCD or MIMXRT1062 eLCDIF).
Use ``tft_pins`` + ``tft_timings`` dicts; ``mp_pin_wrap = true`` on mimxrt for
``Pin("GPIO_…")`` literals. Complex panel init (Qualia, T-RGB) belongs in
``mp_preamble`` / ``cp_preamble``.

```toml
kind = "fbdisplay_rgbframebuffer"
slug = "mimxrt1060_evk_rk043_rgb"
port = "mimxrt1062"
mp_pin_wrap = true
mp_lcd_reset_pulse = true
cp_native_rgbframebuffer = true   # CP imports rgbframebuffer directly

[tft_pins.mp]
de = "GPIO_B0_01"
data = ["GPIO_B0_04", "GPIO_B0_05", ...]

[tft_timings]
frequency = 9_000_000
width = 480
height = 272
```

## Schema — epaper (`epaperdisplay.toml`)

Each `[[board]]` row describes one e-paper CP+MP pair. Optional nested tables:

- `[board.cp]` — CP-only chip kwargs (e.g. `ram_offset = 1`)
- `[board.mp_bus]` / `[board.cp_bus]` — non-default SPI / FourWire pinout
- `template = "magtag"` — MagTag keypad + custom EPD wiring
- `class = "ACeP7In"` when module name differs from driver class

## Schema — pixeldisplay (`kind = "pixeldisplay"`)

NeoPixel or DotStar addressable LED grids. MicroPython uses
``displaysys.pixeldisplay.PixelFramebuffer``; CircuitPython uses
``adafruit_pixel_framebuf.PixelFramebuffer`` from the library bundle.

```toml
kind = "pixeldisplay"
slug = "neopixel_8x4"
title = "NeoPixel 8×4 grid"
strip = "neopixel"              # neopixel | dotstar
out = "pixeldisplay"
circuitpython = true

[grid]
width = 8
height = 4
alternating = false               # serpentine rows when true

[cp.neopixel]
pin = "board.D6"
brightness = 0.1

[mp.neopixel]
pin = 6
bpp = 3
timing = 1
```

DotStar variant uses `[cp.dotstar]` / `[mp.dotstar]` with `clock` and `data` pins
instead of `[cp.neopixel]` / `[mp.neopixel]`.
