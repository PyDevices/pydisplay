"""SH1107 128x64 OLED — CircuitPython"""

import board
from displayio import release_displays
from i2cdisplaybus import I2CDisplayBus
from sh1107 import SH1107

import eventsys

release_displays()

display_bus = I2CDisplayBus(board.I2C(), device_address=0x3C)

display_drv = SH1107(
    display_bus,
    width=128,
    height=64,
    rotation=0,
)

broker = eventsys.Broker()
broker.register_quit_cleanup(display_drv)
