"""Adafruit FeatherWing OLED 128x32 SSD1306 — MicroPython (requires I2C display bus)"""

# MicroPython parity pending i2cbus user_c_module — see docs/hardware/display-interfaces.md

from ssd1306 import SSD1306

import eventsys

raise NotImplementedError(
    "I2C OLED on MicroPython requires i2cbus — use cp_ssd1306_oled_featherwing on CircuitPython"
)
