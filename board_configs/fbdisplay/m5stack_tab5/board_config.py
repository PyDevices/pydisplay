"""M5Stack Tab5 — MicroPython (ESP32-P4 + MIPI DSI)

5″ 1280×720 IPS MIPI DSI + GT911 touch (early Tab5 hardware with ILI9881C).

Product: https://docs.m5stack.com/en/core/Tab5
CP board: https://circuitpython.org/board/m5stack_tab5/

**Hardware revisions:** panels shipped after ~2024-09 use integrated **ST7123**
display/touch — this config targets **ILI9881C + GT911 @ 0x14** (detectable via
I2C). ST7123 Tab5 units need CP firmware or a future ST7123 init table.

Requires displayif ``mipidsi`` on ESP32-P4 firmware
(``./build_mp.sh --port esp32 --board ESP32_GENERIC_P4 --variant C6_WIFI``).

CircuitPython sibling: ``cp_m5stack_tab5``.
"""

from gt911 import GT911
from machine import I2C, Pin
import time

from displaysys.fbdisplay import FBDisplay
from pi4ioe5v import tab5_init_lcd_reset
from tab5_ili9881c_init import TAB5_ILI9881C_INIT
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

i2c = I2C(0, scl=Pin(I2C_SCL), sda=Pin(I2C_SDA), freq=400_000)
tab5_init_lcd_reset(i2c)
time.sleep_ms(100)

# ILI9881C + Goodix GT911 path (CircuitPython board.c detection: 0x14 on I2C)
bus = Bus(frequency=730_000_000, num_lanes=2)

fb = Display(
    bus,
    init_sequence=TAB5_ILI9881C_INIT,
    width=720,
    height=1280,
    color_depth=16,
    pixel_clock_frequency=60_000_000,
    hsync_pulse_width=40,
    hsync_front_porch=40,
    hsync_back_porch=140,
    vsync_pulse_width=4,
    vsync_front_porch=20,
    vsync_back_porch=20,
    backlight_pin=LCD_BACKLIGHT,
    backlight_on_high=True,
)

touch_drv = GT911(
    i2c,
    reset_pin=None,
    irq_pin=TOUCH_INT,
    address=0x14,
    width=720,
    height=1280,
    touch_points=5,
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
