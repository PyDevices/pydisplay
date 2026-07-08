"""Adafruit 0.96" SSD1331 color OLED — CircuitPython"""

import board
from displayio import release_displays
from fourwire import FourWire
from ssd1331 import SSD1331

import eventsys

release_displays()

display_bus = FourWire(
    board.SPI(),
    command=board.D6,
    chip_select=board.D5,
    baudrate=16_000_000,
    reset=board.D9,
)

display_drv = SSD1331(
    display_bus,
    width=96,
    height=64,
    rotation=0,
)
runtime = None
