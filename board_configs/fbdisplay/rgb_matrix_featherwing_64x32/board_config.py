"""Adafruit RGB Matrix FeatherWing 64x32 — MicroPython (Feather ESP32-S3)"""

import rgbmatrix

from displaysys.fbdisplay import FBDisplay
import eventsys

matrix = rgbmatrix.RGBMatrix(
    width=64,
    height=32,
    bit_depth=4,
    rgb_pins=(18, 17, 16, 15, 14, 8),
    addr_pins=(6, 9, 10, 11),
    clock_pin=12,
    latch_pin=0,
    output_enable_pin=1,
)

display_drv = FBDisplay(matrix, width=64, height=32)

runtime = None
