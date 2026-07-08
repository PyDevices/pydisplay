"""Adafruit UC8151D 2.9" flexible E-Ink breakout — CircuitPython"""

import board
from displayio import release_displays
from fourwire import FourWire
from uc8151d import UC8151D

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
_epaper = UC8151D(
    display_bus,
    width=128,
    height=296,
    busy_pin=board.D7,
    rotation=0,
)

display_drv = EPaperDisplay(_epaper, width=128, height=296, color_depth=1)

runtime = None
