"""Adafruit IL0398 4.2" monochrome E-Ink — CircuitPython"""

import board
from displayio import release_displays
from fourwire import FourWire
from il0398 import IL0398

from displaysys.epaperdisplay import EPaperDisplay
import eventsys

release_displays()

display_bus = FourWire(
    board.SPI(),
    command=board.D9,
    chip_select=board.D10,
    reset=board.D6,
    baudrate=4_000_000,
)
_epaper = IL0398(
    display_bus,
    width=400,
    height=300,
    busy_pin=board.D7,
    rotation=0,
)

display_drv = EPaperDisplay(_epaper, width=400, height=300, color_depth=1)

runtime = None
