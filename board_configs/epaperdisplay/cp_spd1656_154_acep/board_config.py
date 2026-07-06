"""Adafruit SPD1656 1.54" 6-color ACeP — CircuitPython"""

import board
from displayio import release_displays
from fourwire import FourWire
from spd1656 import SPD1656

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

_epaper = SPD1656(
    display_bus,
    width=152,
    height=152,
    busy_pin=board.D7,
    rotation=0,
)

display_drv = EPaperDisplay(_epaper, width=152, height=152, color_depth=4)

broker = eventsys.Broker()
broker.register_quit_cleanup(display_drv)
