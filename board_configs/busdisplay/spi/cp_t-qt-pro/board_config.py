"""LILYGO T-QT Pro GC9107 128x128 — CircuitPython"""

import board
from displayio import release_displays
from fourwire import FourWire
from gc9a01 import GC9A01

import eventsys

release_displays()

display_bus = FourWire(
    board.SPI(),
    command=board.GP6,
    chip_select=board.GP5,
    baudrate=60_000_000,
    reset=board.GP1,
)

display_drv = GC9A01(
    display_bus,
    width=128,
    height=128,
    colstart=0,
    rowstart=0,
    rotation=180,
    mirrored=False,
    color_depth=16,
    bgr=True,
    reverse_bytes_in_word=True,
    invert=True,
    brightness=1.0,
    backlight_pin=board.GP10,
    backlight_on_high=True,
)
runtime = None
