"""Adafruit RGB Matrix FeatherWing 64x32 — MicroPython (Feather ESP32-S3)"""

from machine import Pin
import rgbmatrix

from displaysys.fbdisplay import FBDisplay
import eventsys

matrix = rgbmatrix.RGBMatrix(
    width=64,
    height=32,
    bit_depth=4,
    rgb_pins=(Pin(18), Pin(17), Pin(16), Pin(15), Pin(14), Pin(8)),
    addr_pins=(Pin(6), Pin(9), Pin(10), Pin(11)),
    clock_pin=Pin(12),
    latch_pin=Pin(0),
    output_enable_pin=Pin(1),
)

display_drv = FBDisplay(matrix, width=64, height=32)

runtime = None
