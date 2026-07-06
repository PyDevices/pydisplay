"""Waveshare Pico-LCD-1.8 128x160 ST7735R — CircuitPython"""

import board
from displayio import release_displays
from fourwire import FourWire
from st7735r_1 import ST7735R

import eventsys

release_displays()

display_bus = FourWire(
    board.SPI(),
    command=board.GP8,
    chip_select=board.GP9,
    reset=board.GP12,
    baudrate=60_000_000,
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
    backlight_pin=board.GP13,
    backlight_on_high=True,
    reset_high=False,
)

broker = eventsys.Broker()
broker.register_quit_cleanup(display_drv)
