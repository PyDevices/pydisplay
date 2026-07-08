"""Adafruit 1.5" SSD1351 color OLED — CircuitPython"""

import board
from displayio import release_displays
from fourwire import FourWire
from ssd1351 import SSD1351

import eventsys

release_displays()

display_bus = FourWire(
    board.SPI(),
    command=board.D6,
    chip_select=board.D5,
    baudrate=24_000_000,
    reset=board.D9,
)

display_drv = SSD1351(
    display_bus,
    width=128,
    height=128,
    rotation=0,
)
runtime = None
