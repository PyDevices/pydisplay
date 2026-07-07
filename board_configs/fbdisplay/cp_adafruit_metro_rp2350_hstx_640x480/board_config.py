"""Adafruit Metro RP2350 + HSTX DVI breakout — CircuitPython

https://learn.adafruit.com/adafruit-metro-rp2350/hstx-display
"""

import board
import displayio
import picodvi

from displaysys.fbdisplay import FBDisplay
import eventsys

displayio.release_displays()

fb = picodvi.Framebuffer(
    width=640,
    height=480,
    color_depth=8,
    clk_dp=board.CKP,
    clk_dn=board.CKN,
    red_dp=board.D0P,
    red_dn=board.D0N,
    green_dp=board.D1P,
    green_dn=board.D1N,
    blue_dp=board.D2P,
    blue_dn=board.D2N,
)

display_drv = FBDisplay(fb)

broker = eventsys.Broker()
broker.register_quit_cleanup(display_drv)
