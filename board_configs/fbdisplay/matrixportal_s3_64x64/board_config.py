"""MatrixPortal S3 64x64 HUB75 — MicroPython"""

import rgbmatrix

from displaysys.fbdisplay import FBDisplay
import eventsys

matrix = rgbmatrix.RGBMatrix(
    width=64,
    height=64,
    bit_depth=4,
    rgb_pins=(42, 41, 40, 38, 39, 37),
    addr_pins=(45, 36, 48, 35, 21),
    clock_pin=2,
    latch_pin=47,
    output_enable_pin=14,
    doublebuffer=True,
)

display_drv = FBDisplay(matrix, width=64, height=64)

runtime = None
