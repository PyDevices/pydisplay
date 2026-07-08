"""BPI Centi-S3 170x320 ST7789 I80 — CircuitPython"""

import board
from displayio import release_displays
from paralleldisplaybus import ParallelBus
from st7789 import ST7789

import eventsys

release_displays()

display_bus = ParallelBus(
    board.GP8,
    board.GP9,
    board.GP10,
    board.GP11,
    board.GP12,
    board.GP13,
    board.GP14,
    board.GP15,
    board.GP5,
    board.GP4,
    board.GP6,
)

display_drv = ST7789(
    display_bus,
    width=170,
    height=320,
    colstart=35,
    rowstart=0,
    rotation=0,
    mirrored=False,
    color_depth=16,
    bgr=False,
    reverse_bytes_in_word=True,
    invert=True,
    brightness=1.0,
    backlight_pin=board.GP2,
    backlight_on_high=True,
    reset_pin=board.GP3,
    reset_high=True,
)

runtime = None
