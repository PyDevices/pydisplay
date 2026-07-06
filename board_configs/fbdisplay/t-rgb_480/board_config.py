"""LilyGO T-RGB 480×480 ST7701 — MicroPython (ESP32-S3)

ST7701 register init uses bit-banged 3-wire SPI via the XL9535 expander.
RGB565 scanout requires a parallel panel driver from ``pydevices/displayif``
(generated from this config — not the LilyGO ``lcd`` module).
"""

from machine import I2C, Pin

from xl9535 import XL9535
from st7701 import LCDPins, run_init
from displaysys.rgbdisplay import RGBDisplay
import eventsys

_PWR_EN = 2
_LCD_CS = 3
_LCD_SDA = 4
_LCD_CLK = 5
_LCD_RST = 6

# ESP32-S3 RGB data pins (LilyGO T-RGB schematic / tft_config.py reference)
_TRGB_DATA_PINS = (7, 6, 5, 3, 2, 14, 13, 12, 11, 10, 9, 21, 18, 17, 16, 15)
_TRGB_HSYNC = 47
_TRGB_VSYNC = 41
_TRGB_DE = 45
_TRGB_PCLK = 42
_TRGB_BACKLIGHT = 46


def _open_rgb_panel():
    """Open RGB565 parallel panel via pydevices/displayif."""
    try:
        from displayif.rgb565 import RGB565Panel
    except ImportError:
        try:
            from rgb565 import RGB565Panel
        except ImportError as exc:
            raise NotImplementedError(
                "T-RGB pixel output requires pydevices/displayif RGB565 panel driver "
                "(ESP32-S3; generated from board_configs/fbdisplay/t-rgb_480)"
            ) from exc
    return RGB565Panel(
        data=tuple(Pin(p) for p in _TRGB_DATA_PINS),
        hsync=Pin(_TRGB_HSYNC),
        vsync=Pin(_TRGB_VSYNC),
        de=Pin(_TRGB_DE),
        pclk=Pin(_TRGB_PCLK),
        backlight=Pin(_TRGB_BACKLIGHT),
        width=480,
        height=480,
    )


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

rgb_panel = _open_rgb_panel()
display_drv = RGBDisplay(rgb_panel, width=480, height=480, color_depth=16)

broker = eventsys.Broker()
broker.register_quit_cleanup(display_drv)
