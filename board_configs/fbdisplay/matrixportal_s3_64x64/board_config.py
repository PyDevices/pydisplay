"""MatrixPortal S3 64x64 HUB75 — MicroPython"""

from machine import Pin
import rgbmatrix

from displaysys.fbdisplay import FBDisplay
import eventsys

matrix = rgbmatrix.RGBMatrix(
    width=64,
    height=64,
    bit_depth=4,
    rgb_pins=(Pin(42), Pin(41), Pin(40), Pin(38), Pin(39), Pin(37)),
    addr_pins=(Pin(45), Pin(36), Pin(48), Pin(35), Pin(21)),
    clock_pin=Pin(2),
    latch_pin=Pin(47),
    output_enable_pin=Pin(14),
    doublebuffer=True,
)

display_drv = FBDisplay(matrix, width=64, height=64)

runtime = None
