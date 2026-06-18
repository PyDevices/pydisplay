"""
GPL-3.0 License
see https://github.com/Xinyuan-LilyGO/lilygo-micropython/tree/master/target/esp32s3/boards/LILYGO_T-RGB/modules
"""

try:
    from displaysys.busdisplay import BusDisplay
except ImportError:
    from busdisplay import BusDisplay
from time import sleep_ms

_INIT_SEQUENCE = [
    (0xFF, b"\x77\x01\x00\x00\x10", 0),
    (0xC0, b"\x3b\x00", 0),
    (0xC1, b"\x0b\x02", 0),
    (0xC2, b"\x07\x02", 0),
    (0xCC, b"\x10", 0),
    (0xCD, b"\x08", 0),  # 用565时屏蔽    666打开
    (0xB0, b"\x00\x11\x16\x0e\x11\x06\x05\x09\x08\x21\x06\x13\x10\x29\x31\x18", 0),
    (0xB1, b"\x00\x11\x16\x0e\x11\x07\x05\x09\x09\x21\x05\x13\x11\x2a\x31\x18", 0),
    (0xFF, b"\x77\x01\x00\x00\x11", 0),
    (0xB0, b"\x6d", 0),
    (0xB1, b"\x37", 0),
    (0xB2, b"\x81", 0),
    (0xB3, b"\x80", 0),
    (0xB5, b"\x43", 0),
    (0xB7, b"\x85", 0),
    (0xB8, b"\x20", 0),
    (0xC1, b"\x78", 0),
    (0xC2, b"\x78", 0),
    (0xC3, b"\x8c", 0),
    (0xD0, b"\x88", 0),
    (0xE0, b"\x00\x00\x02", 0),
    (0xE1, b"\x03\xa0\x00\x00\x04\xa0\x00\x00\x00\x20\x20", 0),
    (0xE2, b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00", 0),
    (0xE3, b"\x00\x00\x11\x00", 0),
    (0xE4, b"\x22\x00", 0),
    (0xE5, b"\x05\xec\xa0\xa0\x07\xee\xa0\xa0\x00\x00\x00\x00\x00\x00\x00\x00", 0),
    (0xE6, b"\x00\x00\x11\x00", 0),
    (0xE7, b"\x22\x00", 0),
    (0xE8, b"\x06\xed\xa0\xa0\x08\xef\xa0\xa0\x00\x00\x00\x00\x00\x00\x00\x00", 0),
    (0xEB, b"\x00\x00\x40\x40\x00\x00\x00", 0),
    (0xED, b"\xff\xff\xff\xba\x0a\xbf\x45\xff\xff\x54\xfb\xa0\xab\xff\xff\xff", 0),
    (0xEF, b"\x10\x0d\x04\x08\x3f\x1f", 0),
    (0xFF, b"\x77\x01\x00\x00\x13", 0),
    (0xEF, b"\x08", 0),
    (0xFF, b"\x77\x01\x00\x00\x00", 0),
    (0x36, b"\x08", 0),
    (0x3A, b"\x66", 0),
    (0x11, b"\x00", 100),
    # (0xFF,  b'\x77\x01\x00\x00\x12', 0),
    # (0xd1,  b'\x81', 0),
    # (0xd2,  b'\x06', 0),
    (0x29, b"\x00", 120),
]


class LCDPins:
    def __init__(self, *, pwr_en, cs, sda, clk, rst):
        self.pwr_en = pwr_en
        self.cs = cs
        self.sda = sda
        self.clk = clk
        self.rst = rst


class ST7701(BusDisplay):
    """
    ST7701 display driver

    :param lcd_pins: the io pins to configure the display
    """

    def __init__(self, lcd_pins, bus, **kwargs):
        self.lcd_pins = lcd_pins

        self.lcd_pins.pwr_en(1)
        self.lcd_pins.cs(1)
        self.lcd_pins.sda(1)
        self.lcd_pins.clk(1)

        # Reset the display
        self.lcd_pins.rst(1)
        sleep_ms(200)
        self.lcd_pins.rst(0)
        sleep_ms(200)
        self.lcd_pins.rst(1)
        sleep_ms(200)

        super()._init_(bus, _INIT_SEQUENCE, **kwargs)

    def init(self):
        #         self.rotation_table = _ROTATION_TABLE
        super().init(render_mode_full=True)

    def send(self, cmd, params=None):
        self._tx_cmd(cmd)
        if params:
            self._tx_data(params)

    def _tx_cmd(self, cmd):
        self.lcd_pins.cs(0)
        self.lcd_pins.sda(0)
        self.lcd_pins.clk(0)
        self.lcd_pins.clk(1)
        self._tx_byte(cmd)
        self.lcd_pins.cs(1)

    def _tx_data(self, data):
        for i in range(len(data)):
            self.lcd_pins.cs(0)
            self.lcd_pins.sda(1)
            self.lcd_pins.clk(0)
            self.lcd_pins.clk(1)
            self._tx_byte(data[i])
            self.lcd_pins.cs(1)

    def _tx_byte(self, bits):
        for _ in range(8):
            if bits & 0x80:
                self.lcd_pins.sda(1)
            else:
                self.lcd_pins.sda(0)
            bits <<= 1
            self.lcd_pins.clk(0)
            self.lcd_pins.clk(1)
