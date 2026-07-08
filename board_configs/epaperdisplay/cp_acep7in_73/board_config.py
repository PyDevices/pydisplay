"""Adafruit 7.3" ACeP 7-color E-Ink — CircuitPython"""

from acep7in import ACeP7In
import board
from displayio import release_displays
from fourwire import FourWire

from displaysys.epaperdisplay import EPaperDisplay
import eventsys

release_displays()

display_bus = FourWire(
    board.SPI(),
    command=board.D10,
    chip_select=board.D9,
    reset=board.D6,
    baudrate=24_000_000,
)
_epaper = ACeP7In(
    display_bus,
    width=800,
    height=480,
    rotation=0,
)

display_drv = EPaperDisplay(_epaper, width=800, height=480, color_depth=4)

runtime = None
