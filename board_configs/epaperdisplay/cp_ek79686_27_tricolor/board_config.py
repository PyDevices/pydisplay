"""Adafruit EK79686 2.7" tri-color breakout — CircuitPython"""

import board
from displayio import release_displays
from ek79686 import EK79686
from fourwire import FourWire

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
_epaper = EK79686(
    display_bus,
    width=176,
    height=264,
    busy_pin=board.D7,
    rotation=0,
    highlight_color=True,
)

display_drv = EPaperDisplay(_epaper, width=176, height=264, color_depth=2)

runtime = None
