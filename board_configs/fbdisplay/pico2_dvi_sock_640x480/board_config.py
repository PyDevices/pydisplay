"""Raspberry Pi Pico 2 + Adafruit DVI Sock (HSTX) — MicroPython

Plug-in stack:
- Raspberry Pi Pico 2 / Pico 2 W: https://circuitpython.org/board/raspberry_pi_pico2/
- Adafruit DVI Sock for Pico (HSTX differential pairs on GP12–GP19, CK on GP14/15)

Pimoroni Pico DV Demo Base uses a different pin map and is **not** HSTX-compatible on
Pico 2 — use this config with the Adafruit DVI Sock instead.

Targets displayif ``picodvi`` (RP2350 HSTX backend).

CircuitPython sibling: ``cp_pico2_dvi_sock_640x480``.
"""

from machine import Pin

from displaysys.fbdisplay import FBDisplay
import eventsys

try:
    from picodvi import Framebuffer
except ImportError as exc:
    raise NotImplementedError(
        "DVI output requires displayif picodvi cmod (rp2350 HSTX)"
    ) from exc

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

broker = eventsys.Broker()
broker.register_quit_cleanup(display_drv)
