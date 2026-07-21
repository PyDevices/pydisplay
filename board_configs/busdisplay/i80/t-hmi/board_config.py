"""LILYGO T-HMI 240x320 ST7789 I80 + XPT2046 (displayif native esp-lcd i80bus)."""

from i80bus import I80Bus
from machine import SPI, Pin
from st7789 import ST7789
from xpt2046 import Touch

import eventsys

# LilyGO power rails (reed-switch / battery path).
Pin(14, Pin.OUT, value=1)  # PWR_ON
Pin(10, Pin.OUT, value=1)  # PWR_EN

display_bus = I80Bus(
    dc=7,
    cs=6,
    wr=8,
    data=[48, 47, 39, 40, 41, 42, 45, 46],
)

display_drv = ST7789(
    display_bus,
    width=240,
    height=320,
    colstart=0,
    rowstart=0,
    # Portrait: MADCTL BGR (0x08). mirrored=False added MX (0x48) and looked mirrored.
    # Matches TFT_eSPI Setup207 / ST7789 rot0 (no MX/MY) + TFT_BGR.
    rotation=0,
    mirrored=True,
    color_depth=16,
    bgr=True,
    reverse_bytes_in_word=True,
    invert=False,
    brightness=1.0,
    backlight_pin=38,
    backlight_on_high=True,
    reset_pin=None,
    reset_high=True,
    power_pin=None,
    power_on_high=True,
)

# Resistive touch on a dedicated SPI bus (not the parallel LCD).
# Pins: LilyGO pins.h TOUCHSCREEN_*; SPI mode/baud match arduino_xpt2046.
spi = SPI(
    1,
    baudrate=2_000_000,
    polarity=0,
    phase=0,
    sck=Pin(1),
    mosi=Pin(3),
    miso=Pin(4),
)
touch_drv = Touch(
    spi=spi,
    cs=Pin(2),
    int_pin=Pin(9),  # driver enables PULL_UP; IRQ active-low
)

# LilyGO examples/touch/touch.ino default cal (axes inverted vs ascending mins).
# xpt2046.calibrate(orientation=0) swaps width/height args into map size, so pass
# (height, width) to end up with 240x320 mapped coordinates.
touch_drv.calibrate(
    xmin=1788,
    xmax=285,
    ymin=1877,
    ymax=311,
    width=display_drv.height,
    height=display_drv.width,
    orientation=0,
)


# Resistive contacts drop out briefly; keep last point for a few polls so LVGL
# sees a clean down→up instead of a missed click.
_TOUCH_RELEASE_HOLDOFF = 3
_touch_hold = 0
_touch_last = None


def touch_read_func():
    """eventsys: None when up, (x, y) when pressed (single SPI sample)."""
    global _touch_hold, _touch_last
    pt = touch_drv.read_point(clip=True)
    if pt is not None:
        _touch_hold = _TOUCH_RELEASE_HOLDOFF
        _touch_last = pt
        return pt
    if _touch_hold > 0 and _touch_last is not None:
        _touch_hold -= 1
        return _touch_last
    _touch_last = None
    return None


# Button is BOTTOM_MID; taps only registered near the physical top → Y inverted
# vs panel. REVERSE_Y for all portrait/landscape table slots.
_REVERSE_Y = 0b100
touch_rotation_table = (_REVERSE_Y, _REVERSE_Y, _REVERSE_Y, _REVERSE_Y)

runtime = eventsys.Runtime(
    display=display_drv,
    touch_read=touch_read_func,
    touch_rotation_table=touch_rotation_table,
)
