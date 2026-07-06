"""NeoPixel 8x8 matrix (zig-zag / serpentine) — CircuitPython"""

import board
import neopixel
from pixel_framebuffer import create_pixel_framebuffer

from displaysys.pixeldisplay import PixelDisplay
import eventsys

pixels = neopixel.NeoPixel(board.NEOPIXEL, 64, brightness=0.3, auto_write=False)
pixel_buf = create_pixel_framebuffer(
    pixels,
    8,
    8,
    byteorder="GRB",
    rotation=0,
)

display_drv = PixelDisplay(pixel_buf, width=8, height=8, color_depth=24)

broker = eventsys.Broker()
broker.register_quit_cleanup(display_drv)
