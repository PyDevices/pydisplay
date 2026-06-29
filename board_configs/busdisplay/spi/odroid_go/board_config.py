"""ODROID GO with ILI9341 2.4" display"""

from ili9341 import ILI9341
from spibus import SPIBus

display_bus = SPIBus(
    id=2,
    baudrate=60_000_000,
    sck=18,
    mosi=23,
    miso=19,
    dc=21,
    cs=5,
)

display_drv = ILI9341(
    display_bus,
    width=240,
    height=320,
    colstart=0,
    rowstart=0,
    rotation=0,
    mirrored=False,
    color_depth=16,
    bgr=True,
    reverse_bytes_in_word=True,
    invert=False,
    brightness=1.0,
    backlight_pin=14,
    backlight_on_high=True,
    reset_pin=None,
    reset_high=True,
    power_pin=None,
    power_on_high=True,
)

broker = None
