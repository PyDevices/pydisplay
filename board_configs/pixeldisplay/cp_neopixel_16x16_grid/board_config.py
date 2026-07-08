"""NeoPixel 16x16 grid — CircuitPython"""

import board
import neopixel
from pixel_framebuffer import create_pixel_framebuffer

from displaysys.pixeldisplay import PixelDisplay
import eventsys

pixels = neopixel.NeoPixel(board.NEOPIXEL, 256, brightness=0.2, auto_write=False)
pixel_buf = create_pixel_framebuffer(
    pixels,
    16,
    16,
    byteorder="GRB",
    rotation=0,
)

display_drv = PixelDisplay(pixel_buf, width=16, height=16, color_depth=24)

runtime = None
