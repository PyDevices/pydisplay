"""Adafruit FeatherWing OLED 128x32 SSD1306 — CircuitPython"""

import board
from displayio import release_displays
from i2cdisplaybus import I2CDisplayBus
from ssd1306 import SSD1306

import eventsys

release_displays()

display_bus = I2CDisplayBus(board.I2C(), device_address=0x3C)

display_drv = SSD1306(
    display_bus,
    width=128,
    height=32,
    rotation=0,
)

broker = eventsys.Broker()
broker.register_quit_cleanup(display_drv)
