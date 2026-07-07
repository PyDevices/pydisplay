"""NXP MIMXRT1170-EVK + Waveshare 50H-800480-IPS DSI (800×480) on J84 — CircuitPython

Board: https://circuitpython.org/board/nxp_mimxrt1170_evk/
Panel: https://www.waveshare.com/wiki/50H-800480-IPS#Interface_Definition
Waveshare 50H-800480-IPS on J84 (15-pin RPi-style FFC) + 5 V on J85.
"""

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

# Empty init: displayif runs TC358762 bridge setup (RPi / Waveshare 50H-800480-IPS).
PANEL_INIT_SEQUENCE = b""

bus = Bus(frequency=1_000_000_000, num_lanes=2)

fb = Display(
    bus,
    init_sequence=PANEL_INIT_SEQUENCE,
    width=800,
    height=480,
    color_depth=16,
    pixel_clock_frequency=25_979_400,
    hsync_pulse_width=2,
    hsync_front_porch=1,
    hsync_back_porch=46,
    vsync_pulse_width=2,
    vsync_front_porch=7,
    vsync_back_porch=21,
)

display_drv = FBDisplay(fb)

broker = eventsys.Broker()
broker.register_quit_cleanup(display_drv)
