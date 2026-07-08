"""NeoPixel 8x4 grid — CircuitPython NeoPixel grid"""

from adafruit_pixel_framebuf import PixelFramebuffer
import board
import neopixel

from displaysys.pixeldisplay import PixelDisplay

pixel_width = 8
pixel_height = 4

pixels = neopixel.NeoPixel(
    board.D6,
    pixel_width * pixel_height,
    brightness=0.1,
    auto_write=False,
)

_pixel_framebuf = PixelFramebuffer(
    pixels,
    pixel_width,
    pixel_height,
    alternating=False,
)

display_drv = PixelDisplay(_pixel_framebuf)

runtime = None
