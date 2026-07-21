"""
see https://github.com/Xinyuan-LilyGO/lilygo-micropython/tree/master/target/esp32s3/boards/LILYGO_T-RGB/modules
"""

try:
    from displaysys.busdisplay import BusDisplay
except ImportError:
    from busdisplay import BusDisplay


_INIT_SEQUENCE = [
    (0x11, b"\x00", 120),  # Exit sleep mode
    (0x13, b"\x00", 0),  # Turn on the display
    (0xB6, b"\x0a\x82", 0),  # Set display function control
    (0x3A, b"\x55", 10),  # COLMOD: 16 bits per pixel (RGB565)
    (0xB2, b"\x0c\x0c\x00\x33\x33", 0),  # Set porch control
    (0xB7, b"\x35", 0),  # Set gate control
    (0xBB, b"\x28", 0),  # Set VCOMS setting
    (0xC0, b"\x0c", 0),  # Set power control 1
    (0xC2, b"\x01\xff", 0),  # Set power control 2
    (0xC3, b"\x10", 0),  # Set power control 3
    (0xC4, b"\x20", 0),  # Set power control 4
    (0xC6, b"\x0f", 0),  # Set VCOM control 1
    (0xD0, b"\xa4\xa1", 0),  # Set power control A
    # Set gamma curve positive polarity
    (0xE0, b"\xd0\x00\x02\x07\x0a\x28\x32\x44\x42\x06\x0e\x12\x14\x17", 0),
    # Set gamma curve negative polarity
    (0xE1, b"\xd0\x00\x02\x07\x0a\x28\x31\x54\x47\x0e\x1c\x17\x1b\x1e", 0),
    (0x21, b"\x00", 0),  # Enable display inversion
    (0x29, b"\x00", 120),  # Turn on the display
]


class ST7789(BusDisplay):
    """
    ST7789 display driver
    """

    def __init__(self, bus, **kwargs):
        super().__init__(bus, _INIT_SEQUENCE, **kwargs)
