"""SSD1351 1.5" color OLED — MicroPython (Feather breakout pinout)"""

from spibus import SPIBus
from ssd1351 import SSD1351

import eventsys

display_bus = SPIBus(
    id=0,
    baudrate=24_000_000,
    sck=18,
    mosi=19,
    miso=-1,
    dc=6,
    cs=5,
    reset=9,
)

display_drv = SSD1351(
    display_bus,
    width=128,
    height=128,
    rotation=0,
)
runtime = None
