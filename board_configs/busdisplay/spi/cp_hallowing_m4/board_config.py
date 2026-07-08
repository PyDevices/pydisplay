"""Adafruit HalloWing M4 ST7735 240x240 — CircuitPython"""

import board
from displayio import release_displays
from fourwire import FourWire
from st7735 import ST7735

import eventsys

release_displays()

display_bus = FourWire(
    board.SPI(),
    command=board.TFT_DC,
    chip_select=board.TFT_CS,
    baudrate=24_000_000,
    reset=board.TFT_RESET,
)

display_drv = ST7735(
    display_bus,
    width=240,
    height=240,
    colstart=0,
    rowstart=0,
    rotation=0,
    mirrored=False,
    color_depth=16,
    bgr=True,
    reverse_bytes_in_word=True,
)
runtime = None
