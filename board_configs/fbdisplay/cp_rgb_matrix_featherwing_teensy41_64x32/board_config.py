"""Adafruit RGB Matrix FeatherWing 64x32 - CircuitPython (Teensy 4.1)

MicroPython sibling: ``rgb_matrix_featherwing_teensy41_64x32``.
"""

import board
import displayio
import rgbmatrix

from displaysys.fbdisplay import FBDisplay
import eventsys

displayio.release_displays()

matrix = rgbmatrix.RGBMatrix(
    width=64,
    height=32,
    bit_depth=4,
    rgb_pins=[
        board.A0,
        board.A1,
        board.A2,
        board.A3,
        board.A4,
        board.A5,
    ],
    addr_pins=[board.D6, board.D9, board.D10, board.D11],
    clock_pin=board.D12,
    latch_pin=board.D0,
    output_enable_pin=board.D1,
)

display_drv = FBDisplay(matrix, width=64, height=32)

runtime = None
