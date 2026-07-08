"""Adafruit JD79667 3.91" 4-gray E-Ink — CircuitPython"""

import board
from displayio import release_displays
from fourwire import FourWire
from jd79667 import JD79667

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
_epaper = JD79667(
    display_bus,
    width=200,
    height=384,
    busy_pin=board.D7,
    rotation=0,
)

display_drv = EPaperDisplay(_epaper, width=200, height=384, color_depth=2)

runtime = None
