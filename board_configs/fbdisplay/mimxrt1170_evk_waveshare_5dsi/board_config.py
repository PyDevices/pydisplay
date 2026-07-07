"""NXP MIMXRT1170-EVK + Waveshare 5\" DSI (800×480) on J84 — MicroPython

Hardware (plug-in FFC, no breadboard wiring):
- MIMXRT1170-EVK / EVKB: https://circuitpython.org/board/nxp_mimxrt1170_evk/
- Waveshare 5\" DSI LCD (800×480, 15-pin Raspberry Pi-style DSI FFC) on EVK **J84**
- Panel 5 V from EVK **J85** (5 V to pin 1, GND to pin 2) per NXP SDK RPi-panel notes
- Board: 5 V on **J43**, jumper **J38** at 1–2

Uses the same 15-pin DSI connector as the Raspberry Pi 7\" touch display.  The Waveshare
5\" panel is DPI-over-DSI; panel init and DPI timings are supplied when displayif
``mipidsi`` lands for RT1176 (NXP ``fsl_mipi_dsi`` + ``display_support`` panel table).

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

# Placeholder until mimxrt panel driver supplies vendor init (Waveshare / RPi DPI panel).
PANEL_INIT_SEQUENCE = b""

# MIPI DSI bus — 2 lanes, 1 Gbps/lane (tune with displayif driver / NXP BSP)
bus = Bus(frequency=1_000_000_000, num_lanes=2)

# DPI timings for 800×480 @ ~60 Hz (RPi-class panel; refine per panel driver)
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
