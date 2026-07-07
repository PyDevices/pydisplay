"""NXP MIMXRT1170-EVK + Waveshare 5\" DSI (800×480) on J84 — CircuitPython

Board: https://circuitpython.org/board/nxp_mimxrt1170_evk/
Waveshare 5\" DSI on J84 (15-pin RPi-style FFC) + 5 V on J85.
"""

import board
import displayio

from displaysys.fbdisplay import FBDisplay
import eventsys

displayio.release_displays()

try:
    from mipidsi import Bus, Display
except ImportError as exc:
    raise NotImplementedError(
        "MIPI DSI requires displayif mipidsi cmod (mimxrt1176 port)"
    ) from exc

PANEL_INIT_SEQUENCE = b""

bus = mipidsi.Bus(frequency=1_000_000_000, num_lanes=2)

fb = Display(
    bus,
    init_sequence=PANEL_INIT_SEQUENCE,
    width=800,
    height=480,
    color_depth=16,
    pixel_clock_frequency=32_000_000,
    hsync_pulse_width=70,
    hsync_front_porch=40,
    hsync_back_porch=40,
    vsync_pulse_width=10,
    vsync_front_porch=13,
    vsync_back_porch=29,
)

display_drv = FBDisplay(fb)

broker = eventsys.Broker()
broker.register_quit_cleanup(display_drv)
