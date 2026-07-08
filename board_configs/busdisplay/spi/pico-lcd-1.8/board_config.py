"""Waveshare Pico-LCD-1.8 128x160 ST7735S display"""

from spibus import SPIBus
from st7735r_1 import ST7735R

import eventsys

display_bus = SPIBus(
    id=1,
    baudrate=60_000_000,
    sck=10,
    mosi=11,
    dc=8,
    cs=9,
)

display_drv = ST7735R(
    display_bus,
    width=160,
    height=128,
    colstart=1,
    rowstart=2,
    rotation=0,
    mirrored=False,
    color_depth=16,
    bgr=True,
    reverse_bytes_in_word=True,
    invert=False,
    brightness=1.0,
    backlight_pin=13,
    backlight_on_high=True,
    reset_pin=12,
    reset_high=False,
    power_pin=None,
    power_on_high=True,
    cp={
        "width": 160,
        "height": 128,
        "colstart": 1,
        "rowstart": 2,
        "rotation": 0,
        "mirrored": False,
        "color_depth": 16,
        "bgr": True,
        "reverse_bytes_in_word": True,
        "invert": False,
        "brightness": 1.0,
        "backlight_pin": "board.GP13",
        "backlight_on_high": True,
        "reset_high": False,
    },
)
runtime = None
