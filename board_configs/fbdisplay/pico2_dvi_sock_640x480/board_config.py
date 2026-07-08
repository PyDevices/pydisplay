"""Raspberry Pi Pico 2 + Adafruit DVI Sock (HSTX) - MicroPython"""

from machine import Pin

from displaysys.fbdisplay import FBDisplay
import eventsys

try:
    from picodvi import Framebuffer
except ImportError as exc:
    raise NotImplementedError("DVI output requires displayif picodvi cmod (rp2350 HSTX)") from exc

fb = Framebuffer(
    width=640,
    height=480,
    color_depth=8,
    clk_dp=Pin(14),
    clk_dn=Pin(15),
    red_dp=Pin(12),
    red_dn=Pin(13),
    green_dp=Pin(18),
    green_dn=Pin(19),
    blue_dp=Pin(16),
    blue_dn=Pin(17),
)

display_drv = FBDisplay(fb)

runtime = None
