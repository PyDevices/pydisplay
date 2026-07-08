"""MatrixPortal M4 64x32 HUB75 — MicroPython"""

from machine import Pin
import rgbmatrix

from displaysys.fbdisplay import FBDisplay
import eventsys

matrix = rgbmatrix.RGBMatrix(
    width=64,
    height=32,
    bit_depth=4,
    rgb_pins=(
        Pin("PB00"),
        Pin("PB01"),
        Pin("PB02"),
        Pin("PB03"),
        Pin("PB04"),
        Pin("PB05"),
    ),
    addr_pins=(Pin("PB07"), Pin("PB08"), Pin("PB09"), Pin("PB15")),
    clock_pin=Pin("PB06"),
    latch_pin=Pin("PB14"),
    output_enable_pin=Pin("PB12"),
    doublebuffer=True,
)

display_drv = FBDisplay(matrix, width=64, height=32)

runtime = None
