"""LilyGo T-Embed ST7789 170x320 — CircuitPython"""

import board
from displayio import release_displays
from fourwire import FourWire
from st7789 import ST7789

import eventsys

release_displays()

display_bus = FourWire(
    board.SPI(),
    command=board.D13,
    chip_select=board.D10,
    baudrate=60_000_000,
)

display_drv = ST7789(
    display_bus,
    width=170,
    height=320,
    colstart=0,
    rowstart=0,
    rotation=0,
    mirrored=False,
    color_depth=16,
    bgr=False,
    reverse_bytes_in_word=True,
    invert=False,
    brightness=1.0,
    backlight_pin=board.D15,
    backlight_on_high=True,
)

broker = eventsys.Broker()
broker.register_quit_cleanup(display_drv)
