"""LilyGO T-RGB 480×480 ST7701 — MicroPython (ESP32-S3 + lcd.DPI)"""

from machine import I2C, Pin

try:
    from lcd import DPI
except ImportError as exc:
    raise NotImplementedError(
        "T-RGB requires the LilyGO lcd.DPI module (ESP32-S3 MicroPython firmware)"
    ) from exc

from xl9535 import XL9535
from st7701 import LCDPins, run_init
from displaysys.dpidisplay import DPIDisplay
import eventsys

_PWR_EN = 2
_LCD_CS = 3
_LCD_SDA = 4
_LCD_CLK = 5
_LCD_RST = 6

i2c = I2C(0, scl=Pin(48), sda=Pin(8))
xl = XL9535(i2c)
_pin_mask = (1 << _PWR_EN) | (1 << _LCD_CS) | (1 << _LCD_SDA) | (1 << _LCD_CLK) | (1 << _LCD_RST)
xl.pinMode8(0, _pin_mask, xl.OUT)
xl.digitalWrite(_PWR_EN, 1)

lcd_pins = LCDPins(
    pwr_en=xl.Pin(_PWR_EN, xl.OUT, value=1),
    cs=xl.Pin(_LCD_CS, xl.OUT, value=1),
    sda=xl.Pin(_LCD_SDA, xl.OUT, value=1),
    clk=xl.Pin(_LCD_CLK, xl.OUT, value=1),
    rst=xl.Pin(_LCD_RST, xl.OUT, value=1),
)
run_init(lcd_pins)

rgb = DPI(
    data=(
        Pin(7),
        Pin(6),
        Pin(5),
        Pin(3),
        Pin(2),
        Pin(14),
        Pin(13),
        Pin(12),
        Pin(11),
        Pin(10),
        Pin(9),
        Pin(21),
        Pin(18),
        Pin(17),
        Pin(16),
        Pin(15),
    ),
    hsync=Pin(47),
    vsync=Pin(41),
    de=Pin(45),
    pclk_pin=Pin(42),
    timings=(1, 30, 50, 1, 30, 20),
    backlight=Pin(46),
    pclk=10_000_000,
    width=480,
    height=480,
)

display_drv = DPIDisplay(rgb, width=480, height=480, color_depth=16)

broker = eventsys.Broker()
broker.register_quit_cleanup(display_drv)
