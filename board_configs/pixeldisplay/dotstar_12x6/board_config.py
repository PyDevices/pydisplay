"""DotStar 12x6 grid — MicroPython DotStar grid"""

import dotstar
from machine import Pin

from displaysys.pixeldisplay import PixelDisplay, PixelFramebuffer

pixel_width = 12
pixel_height = 6

pixels = dotstar.DotStar(Pin(13), Pin(11), pixel_width * pixel_height, bpp=3)

_pixel_framebuf = PixelFramebuffer(pixels, pixel_width, pixel_height, alternating=False)
display_drv = PixelDisplay(_pixel_framebuf)

runtime = None
