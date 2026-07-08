"""LilyGO T-Display-S3 170x320 ST7789 I80 — CircuitPython"""

import board
from displayio import release_displays
from paralleldisplaybus import ParallelBus
from st7789 import ST7789

import eventsys

release_displays()

display_bus = ParallelBus(
    board.D39,
    board.D40,
    board.D41,
    board.D42,
    board.D45,
    board.D46,
    board.D47,
    board.D48,
    board.D7,
    board.D6,
    board.D8,
)

display_drv = ST7789(
    display_bus,
    width=170,
    height=320,
    colstart=0,
    rowstart=35,
    rotation=0,
    mirrored=False,
    color_depth=16,
    bgr=False,
    reverse_bytes_in_word=True,
    invert=True,
    brightness=1.0,
    backlight_pin=board.D38,
    backlight_on_high=True,
)
runtime = None
