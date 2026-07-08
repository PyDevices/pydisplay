"""Adafruit RGB Matrix FeatherWing 64x32 — MicroPython (Teensy 4.1)

CircuitPython sibling: ``cp_rgb_matrix_featherwing_teensy41_64x32``.
"""

from machine import Pin
import rgbmatrix

from displaysys.fbdisplay import FBDisplay
import eventsys

matrix = rgbmatrix.RGBMatrix(
    width=64,
    height=32,
    bit_depth=4,
    rgb_pins=(
        Pin("A0"),
        Pin("A1"),
        Pin("A2"),
        Pin("A3"),
        Pin("A4"),
        Pin("A5"),
    ),
    addr_pins=(Pin("D6"), Pin("D9"), Pin("D10"), Pin("D11")),
    clock_pin=Pin("D12"),
    latch_pin=Pin("D0"),
    output_enable_pin=Pin("D1"),
)

display_drv = FBDisplay(matrix, width=64, height=32)

runtime = None
