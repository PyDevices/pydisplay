"""SSD1331 0.96\" OLED — MicroPython (Feather breakout pinout)"""

from spibus import SPIBus
from ssd1331 import SSD1331

import eventsys

display_bus = SPIBus(
    id=0,
    baudrate=16_000_000,
    sck=18,
    mosi=19,
    miso=-1,
    dc=6,
    cs=5,
    reset=9,
)

display_drv = SSD1331(
    display_bus,
    width=96,
    height=64,
    rotation=0,
)

broker = eventsys.Broker()
broker.register_quit_cleanup(display_drv)
