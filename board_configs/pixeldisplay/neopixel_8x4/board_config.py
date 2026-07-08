"""NeoPixel 8x4 grid — MicroPython NeoPixel grid"""

from machine import Pin
import neopixel

from displaysys.pixeldisplay import PixelDisplay, PixelFramebuffer

pixel_width = 8
pixel_height = 4

pixels = neopixel.NeoPixel(Pin(6), pixel_width * pixel_height, bpp=3, timing=1)

_pixel_framebuf = PixelFramebuffer(pixels, pixel_width, pixel_height, alternating=False)
display_drv = PixelDisplay(_pixel_framebuf)

runtime = None
