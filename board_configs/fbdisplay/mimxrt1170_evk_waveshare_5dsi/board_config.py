"""NXP MIMXRT1170-EVK + Waveshare 50H-800480-IPS DSI (800×480) on J84 — MicroPython

Hardware (plug-in FFC, no breadboard wiring):
- MIMXRT1170-EVK / EVKB: https://circuitpython.org/board/nxp_mimxrt1170_evk/
- Waveshare 50H-800480-IPS: https://www.waveshare.com/wiki/50H-800480-IPS#Interface_Definition
  (15-pin RPi-style DSI FFC on EVK **J84**; 2-lane DSI + clock)
- Panel 5 V from EVK **J85** (5 V to pin 1, GND to pin 2) per NXP SDK RPi-panel notes
- Board: 5 V on **J43**, jumper **J38** at 1–2

On Raspberry Pi this panel uses ``dtoverlay=vc4-kms-dsi-7inch`` (TC358762 DSI-to-DPI
bridge).  displayif ``mipidsi`` programs the bridge automatically when
``init_sequence`` is empty.

CircuitPython sibling: ``cp_mimxrt1170_evk_waveshare_5dsi``.
"""

from displaysys.fbdisplay import FBDisplay
import eventsys

try:
    from mipidsi import Bus, Display
except ImportError as exc:
    raise NotImplementedError(
        "MIPI DSI requires displayif mipidsi cmod (mimxrt1176 port)"
    ) from exc

# Empty init: displayif runs TC358762 bridge setup (RPi / Waveshare 50H-800480-IPS).
PANEL_INIT_SEQUENCE = b""

# 2-lane DSI (Waveshare 50H-800480-IPS pinout: D0 + D1 + clock).
bus = Bus(frequency=1_000_000_000, num_lanes=2)

# DPI timings from Raspberry Pi firmware / panel-raspberrypi-touchscreen (800×480 @ ~60 Hz).
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
