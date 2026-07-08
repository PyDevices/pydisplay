"""Adafruit FeatherWing OLED 128x32 SSD1306 — MicroPython"""

from i2cbus import I2CBus
from machine import I2C, Pin
from ssd1306 import SSD1306

import eventsys

display_bus = I2CBus(I2C(0, sda=Pin(4), scl=Pin(5), freq=400_000), address=0x3C)

display_drv = SSD1306(
    display_bus,
    width=128,
    height=32,
    rotation=0,
)
runtime = None
