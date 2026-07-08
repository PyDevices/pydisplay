"""NXP MIMXRT1170-EVK + Waveshare 50H-800480-IPS DSI (800x480) on J84 - MicroPython"""

from gt911 import GT911
from machine import I2C, Pin

from displaysys.fbdisplay import FBDisplay
import eventsys

try:
    from mipidsi import Bus, Display
except ImportError as exc:
    raise NotImplementedError(
        "MIPI DSI requires displayif mipidsi cmod (mimxrt1176 port)"
    ) from exc

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

display_drv = FBDisplay(fb)

runtime = eventsys.Runtime(
    display=display_drv,
    touch_read=touch_read_func,
    touch_rotation_table=touch_rotation_table,
)
