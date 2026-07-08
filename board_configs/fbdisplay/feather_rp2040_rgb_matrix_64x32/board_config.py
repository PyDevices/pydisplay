"""Adafruit Feather RP2040 + RGB Matrix FeatherWing 64x32 - MicroPython

Plug-in stack (Feather headers only):
- Adafruit Feather RP2040: https://circuitpython.org/board/adafruit_feather_rp2040/
- Adafruit RGB Matrix FeatherWing on Feather socket

Pin map matches CircuitPython ``cp_rgb_matrix_featherwing_64x32``.

CircuitPython sibling: ``cp_feather_rp2040_rgb_matrix_64x32``.
"""

import rgbmatrix

from displaysys.fbdisplay import FBDisplay
import eventsys

matrix = rgbmatrix.RGBMatrix(
    width=64,
    height=32,
    bit_depth=4,
    rgb_pins=(26, 27, 28, 29, 18, 19),  # A0..A3, SCK/MOSI as A4/A5
    addr_pins=(8, 9, 10, 11),  # D6, D9, D10, D11
    clock_pin=12,  # D12
    latch_pin=1,  # D0
    output_enable_pin=0,  # D1
)

display_drv = FBDisplay(matrix, width=64, height=32)

runtime = None
