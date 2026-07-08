"""Pimoroni Pico DV Demo Base + Raspberry Pi Pico (RP2040) - MicroPython

Plug-in stack (no breadboard wiring):
- Raspberry Pi Pico in socket headers: https://circuitpython.org/board/raspberry_pi_pico/
- Pimoroni Pico DV Demo Base HDMI: https://circuitpython.org/board/pimoroni_pico_dv_base/

DVI pinout matches CircuitPython ``board.CKP`` / ``D0P`` aliases on pimoroni_pico_dv_base
(GP6-GP13).  Targets displayif ``picodvi`` (PIO bit-bang on RP2040).

CircuitPython sibling: ``cp_pimoroni_pico_dv_base_640x480``.
"""

from machine import Pin

from displaysys.fbdisplay import FBDisplay
import eventsys

try:
    from picodvi import Framebuffer
except ImportError as exc:
    raise NotImplementedError(
        "DVI output requires displayif picodvi cmod (rp2 PIO or RP2350 HSTX)"
    ) from exc

fb = Framebuffer(
    width=640,
    height=480,
    color_depth=8,
    clk_dp=Pin(7),
    clk_dn=Pin(6),
    red_dp=Pin(9),
    red_dn=Pin(8),
    green_dp=Pin(11),
    green_dn=Pin(10),
    blue_dp=Pin(13),
    blue_dn=Pin(12),
)

display_drv = FBDisplay(fb)

runtime = None
