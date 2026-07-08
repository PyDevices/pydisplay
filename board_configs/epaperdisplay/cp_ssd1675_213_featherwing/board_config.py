"""Adafruit SSD1675 2.13" monochrome E-Ink FeatherWing — CircuitPython"""

import board
from displayio import release_displays
from fourwire import FourWire
from ssd1675 import SSD1675

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
_epaper = SSD1675(
    display_bus,
    width=250,
    height=122,
    busy_pin=board.D7,
    rotation=0,
)

display_drv = EPaperDisplay(_epaper, width=250, height=122, color_depth=1)

runtime = None
