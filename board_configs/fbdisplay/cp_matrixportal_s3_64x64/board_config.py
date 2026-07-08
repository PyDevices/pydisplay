"""MatrixPortal S3 with 64x64 HUB75 RGB matrix — CircuitPython"""

import board
import displayio
import rgbmatrix

from displaysys.fbdisplay import FBDisplay
import eventsys

displayio.release_displays()

matrix = rgbmatrix.RGBMatrix(
    width=64,
    height=64,
    bit_depth=4,
    rgb_pins=[board.MTX_R1, board.MTX_G1, board.MTX_B1, board.MTX_R2, board.MTX_G2, board.MTX_B2],
    addr_pins=[
        board.MTX_ADDRA,
        board.MTX_ADDRB,
        board.MTX_ADDRC,
        board.MTX_ADDRD,
        board.MTX_ADDRE,
    ],
    clock_pin=board.MTX_CLK,
    latch_pin=board.MTX_LAT,
    output_enable_pin=board.MTX_OE,
    doublebuffer=True,
)

fb = matrix

display_drv = FBDisplay(fb, width=64, height=64)
runtime = None
