"""Adafruit PyPortal — MicroPython"""

from ili9341 import ILI9341
from machine import I2C, Pin
from spibus import SPIBus

import eventsys

raise NotImplementedError(
    "PyPortal on MicroPython requires board-specific SPI/I2C pin defs and TT21100 touch port"
)
