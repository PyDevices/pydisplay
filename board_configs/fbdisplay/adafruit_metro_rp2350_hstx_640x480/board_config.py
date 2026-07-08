"""Adafruit Metro RP2350 + HSTX DVI breakout - MicroPython

Metro RP2350 FPC (GPIO12-19) to Adafruit RP2350 22-pin HSTX→DVI adapter.
Pin map differs from Pico 2 DVI Sock (lane order).

https://learn.adafruit.com/adafruit-metro-rp2350/hstx-display
https://circuitpython.org/board/adafruit_metro_rp2350/

CircuitPython sibling: ``cp_adafruit_metro_rp2350_hstx_640x480``.
"""

from machine import Pin

from displaysys.fbdisplay import FBDisplay
import eventsys

try:
    from picodvi import Framebuffer
except ImportError as exc:
    raise NotImplementedError("DVI output requires displayif picodvi cmod (rp2350 HSTX)") from exc

# Metro RP2350 HSTX (Adafruit learning guide / Metro_RP2350_Breakout/code.py)
fb = Framebuffer(
    width=640,
    height=480,
    color_depth=8,
    clk_dp=Pin(14),
    clk_dn=Pin(15),
    red_dp=Pin(18),
    red_dn=Pin(19),
    green_dp=Pin(16),
    green_dn=Pin(17),
    blue_dp=Pin(12),
    blue_dn=Pin(13),
)

display_drv = FBDisplay(fb)

runtime = None
