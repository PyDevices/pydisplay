"""Wokwi ESP32S3 and ILI9341 Display"""

from ili9341 import ILI9341
from spibus import SPIBus

import eventsys

display_bus = SPIBus(
    id=1,
    baudrate=60_000_000,
    sck=36,
    mosi=35,
    miso=37,
    dc=16,
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
    backlight_pin=None,
    backlight_on_high=True,
    reset_pin=None,
    reset_high=True,
    power_pin=None,
    power_on_high=True,
)
runtime = None
