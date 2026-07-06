"""Adafruit CLUE (built-in ST7789) — CircuitPython"""

import board
from displayio import release_displays
from fourwire import FourWire
from st7789 import ST7789

import eventsys

release_displays()

display_bus = FourWire(
    board.SPI(),
    command=board.TFT_DC,
    chip_select=board.TFT_CS,
    reset=board.TFT_RESET,
    baudrate=24_000_000,
)

display_drv = ST7789(
    display_bus,
    width=240,
    height=240,
    rotation=0,
    colstart=0,
    rowstart=80,
    bgr=False,
    reverse_bytes_in_word=True,
)

broker = eventsys.Broker()
broker.register_quit_cleanup(display_drv)
