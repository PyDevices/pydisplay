"""Adafruit Feather RP2040 + RGB Matrix FeatherWing 64x32 - MicroPython"""

from machine import Pin
import rgbmatrix

from displaysys.fbdisplay import FBDisplay
import eventsys

matrix = rgbmatrix.RGBMatrix(
    width=64,
    height=32,
    bit_depth=4,
    rgb_pins=(Pin(26), Pin(27), Pin(28), Pin(29), Pin(18), Pin(19)),
    addr_pins=(Pin(8), Pin(9), Pin(10), Pin(11)),
    clock_pin=Pin(12),
    latch_pin=Pin(1),
    output_enable_pin=Pin(0),
)

display_drv = FBDisplay(matrix, width=64, height=32)

runtime = None
