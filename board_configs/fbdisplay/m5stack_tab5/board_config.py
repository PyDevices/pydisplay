"""M5Stack Tab5 — MicroPython (ESP32-P4 + MIPI DSI)

5″ 1280×720 IPS MIPI DSI with auto-detected panel/touch:

- **ILI9881C + GT911 @ 0x14** — early Tab5 units (pre ~Oct 2025)
- **ST7123 TDDI @ 0x55** — integrated display/touch (current production)

Product: https://docs.m5stack.com/en/core/Tab5
CP board: https://circuitpython.org/board/m5stack_tab5/

Requires displayif ``mipidsi`` on ESP32-P4 firmware
(``./build_mp.sh --port esp32 --board ESP32_GENERIC_P4 --variant C6_WIFI``).

CircuitPython sibling: ``cp_m5stack_tab5``.
"""

from gt911 import GT911
from machine import I2C, Pin
import time

from displaysys.fbdisplay import FBDisplay
from pi4ioe5v import tab5_init_lcd_reset
from st7123 import ST7123
from tab5_ili9881c_init import TAB5_ILI9881C_INIT
from tab5_st7123_init import TAB5_ST7123_INIT
import eventsys

try:
    from mipidsi import Bus, Display
except ImportError as exc:
    raise NotImplementedError(
        "MIPI DSI requires displayif mipidsi cmod (esp32p4 port)"
    ) from exc

I2C_SCL = 32
I2C_SDA = 31
LCD_BACKLIGHT = 22
TOUCH_INT = 23

GOODIX_ADDR = 0x14
ST7123_ADDR = 0x55

ILI9881C_PROFILE = {
    "bus_mhz": 730_000_000,
    "init": TAB5_ILI9881C_INIT,
    "pclk": 60_000_000,
    "hsync_pulse": 40,
    "hsync_back": 140,
    "hsync_front": 40,
    "vsync_pulse": 4,
    "vsync_back": 20,
    "vsync_front": 20,
}

ST7123_PROFILE = {
    "bus_mhz": 965_000_000,
    "init": TAB5_ST7123_INIT,
    "pclk": 70_000_000,
    "hsync_pulse": 2,
    "hsync_back": 40,
    "hsync_front": 40,
    "vsync_pulse": 2,
    "vsync_back": 8,
    "vsync_front": 220,
}

i2c = I2C(0, scl=Pin(I2C_SCL), sda=Pin(I2C_SDA), freq=400_000)
tab5_init_lcd_reset(i2c)
time.sleep_ms(100)

addrs = set(i2c.scan())
if GOODIX_ADDR in addrs:
    profile = ILI9881C_PROFILE
    touch_drv = GT911(
        i2c,
        reset_pin=None,
        irq_pin=TOUCH_INT,
        address=GOODIX_ADDR,
        width=720,
        height=1280,
        touch_points=5,
    )
elif ST7123_ADDR in addrs:
    profile = ST7123_PROFILE
    touch_drv = ST7123(
        i2c,
        irq_pin=Pin(TOUCH_INT),
        width=720,
        height=1280,
    )
else:
    raise RuntimeError(
        "Tab5 panel not detected on I2C (expected GT911@0x14 or ST7123@0x55)"
    )

bus = Bus(frequency=profile["bus_mhz"], num_lanes=2)

fb = Display(
    bus,
    init_sequence=profile["init"],
    width=720,
    height=1280,
    color_depth=16,
    pixel_clock_frequency=profile["pclk"],
    hsync_pulse_width=profile["hsync_pulse"],
    hsync_front_porch=profile["hsync_front"],
    hsync_back_porch=profile["hsync_back"],
    vsync_pulse_width=profile["vsync_pulse"],
    vsync_front_porch=profile["vsync_front"],
    vsync_back_porch=profile["vsync_back"],
    backlight_pin=LCD_BACKLIGHT,
    backlight_on_high=True,
)


def touch_read_func():
    n, points = touch_drv.read_points()
    if n:
        return points[0][0], points[0][1]
    return None


display_drv = FBDisplay(fb)

touch_rotation_table = (0, 0, 0, 0)

broker = eventsys.Broker()

touch_dev = broker.create(
    type=eventsys.TOUCH,
    read=touch_read_func,
    data=display_drv,
    data2=touch_rotation_table,
)

broker.register_quit_cleanup(display_drv)
