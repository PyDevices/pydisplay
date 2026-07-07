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

Touch (50H-800480-IPS-**CT** capacitive SKU only): Goodix GT911 on I2C via J84 FFC
pins 11–12 (``board.SDA`` / ``board.SCL``, LPI2C5).  Reset and interrupt are routed
on ``board.D9`` / ``board.D6`` per NXP MIPI-panel touch wiring.  The non-touch IPS
variant has no controller on that I2C bus.

CircuitPython sibling: ``cp_mimxrt1170_evk_waveshare_5dsi``.
"""

from gt911 import GT911
from machine import I2C

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

# 50H-800480-IPS-CT: Goodix GT911 on J84 FFC I2C (pins 11–12) + EVK touch GPIOs
i2c = I2C(0, freq=400_000)
touch_drv = GT911(
    i2c,
    reset_pin="GPIO_AD_01",
    irq_pin="GPIO_AD_00",
    width=800,
    height=480,
    touch_points=5,
)


def touch_read_func():
    n, points = touch_drv.read_points()
    if n:
        return points[0][0], points[0][1]
    return None


touch_rotation_table = (0, 0, 0, 0)

broker = eventsys.Broker()

touch_dev = broker.create(
    type=eventsys.TOUCH,
    read=touch_read_func,
    data=display_drv,
    data2=touch_rotation_table,
)

broker.register_quit_cleanup(display_drv)
