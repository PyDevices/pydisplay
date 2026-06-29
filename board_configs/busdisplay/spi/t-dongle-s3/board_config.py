"""LilyGo T-Dongle-S3 80x160 ST7735 display"""

from spibus import SPIBus
from st7735 import ST7735

display_bus = SPIBus(
    id=2,
    baudrate=60_000_000,
    sck=5,
    mosi=3,
    dc=2,
    cs=4,
)

display_drv = ST7735(
    display_bus,
    width=80,
    height=160,
    colstart=0,
    rowstart=0,
    rotation=180,
    mirrored=False,
    color_depth=16,
    bgr=True,
    reverse_bytes_in_word=False,
    invert=True,
    brightness=1.0,
    backlight_pin=38,
    backlight_on_high=True,
    reset_pin=1,
    reset_high=True,
    power_pin=None,
    power_on_high=True,
)

broker = None
