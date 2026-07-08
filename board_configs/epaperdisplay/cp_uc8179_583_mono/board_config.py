"""Adafruit UC8179 5.83" monochrome bare display — CircuitPython"""

import board
from displayio import release_displays
from fourwire import FourWire
from uc8179 import UC8179

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
_epaper = UC8179(
    display_bus,
    width=648,
    height=480,
    busy_pin=board.D7,
    rotation=0,
)

display_drv = EPaperDisplay(_epaper, width=648, height=480, color_depth=1)

runtime = None
