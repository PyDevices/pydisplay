"""LilyGo T-Dongle-S3 80x160 ST7735 — CircuitPython"""

import board
from displayio import release_displays
from fourwire import FourWire
from st7735 import ST7735

import eventsys

release_displays()

display_bus = FourWire(
    board.SPI(),
    command=board.D2,
    chip_select=board.D4,
    baudrate=60_000_000,
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
    backlight_pin=board.D38,
    backlight_on_high=True,
    reset_pin=board.D1,
    reset_high=True,
)
runtime = None
