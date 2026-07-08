"""Adafruit IL0373 2.13" tri-color FeatherWing — CircuitPython"""

import board
from displayio import release_displays
from fourwire import FourWire
from il0373 import IL0373

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
_epaper = IL0373(
    display_bus,
    width=250,
    height=122,
    busy_pin=board.D7,
    rotation=0,
    highlight_color=True,
)

display_drv = EPaperDisplay(_epaper, width=250, height=122, color_depth=2)

runtime = None
