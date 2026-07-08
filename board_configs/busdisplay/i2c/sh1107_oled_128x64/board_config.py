"""SH1107 128x64 OLED — MicroPython"""

from i2cbus import I2CBus
from machine import I2C, Pin
from sh1107 import SH1107

import eventsys

display_bus = I2CBus(I2C(0, sda=Pin(4), scl=Pin(5), freq=400_000), address=0x3C)

display_drv = SH1107(
    display_bus,
    width=128,
    height=64,
    rotation=0,
)
runtime = None
