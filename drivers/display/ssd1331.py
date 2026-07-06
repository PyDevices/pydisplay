try:
    from displaysys.busdisplay import BusDisplay
except ImportError:
    from busdisplay import BusDisplay

# SPDX-FileCopyrightText: 2019 Melissa LeBlanc-Williams for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_ssd1331`
================================================================================

displayio Driver for SSD1331 Displays


* Author(s): Melissa LeBlanc-Williams

Implementation Notes
--------------------

**Hardware:**

* OLED Breakout Board - 16-bit Color 0.96" w/microSD holder:
  https://www.adafruit.com/product/684

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

"""


try:
    import typing

    from fourwire import FourWire
except ImportError:
    pass




_INIT_SEQUENCE = (
    b"\xae\x00"  # _DISPLAYOFF
    b"\xa0\x01\x72"  # _SETREMAP (RGB)
    b"\xa1\x01\x00"  # _STARTLINE
    b"\xa2\x01\x00"  # _DISPLAYOFFSET
    b"\xa4\x00"  # _NORMALDISPLAY
    b"\xa8\x01\x3f"  # _SETMULTIPLEX (1/64 duty)
    b"\xad\x01\x8e"  # _SETMASTER
    b"\xb0\x01\x0b"  # _POWERMODE
    b"\xb1\x01\x31"  # _PRECHARGE
    b"\xb3\x01\xf0"  # _CLOCKDIV 7:4 = Osc Freq, 3:0 = CLK Div Ratio
    b"\x8a\x01\x64"  # _PRECHARGEA
    b"\x8b\x01\x78"  # _PRECHARGEB
    b"\x8c\x01\x64"  # _PRECHARGEC
    b"\xbb\x01\x3a"  # _PRECHARGELEVEL
    b"\xbe\x01\x3e"  # _VCOMH
    b"\x87\x01\x06"  # _MASTERCURRENT
    b"\x81\x01\x91"  # _CONTRASTA
    b"\x82\x01\x50"  # _CONTRASTB
    b"\x83\x01\x7d"  # _CONTRASTC
    b"\xaf\x00"  # _DISPLAYON
)


# pylint: disable=too-few-public-methods
class SSD1331(BusDisplay):
    """SSD1331 driver"""

    def __init__(self, bus: FourWire, **kwargs) -> None:
        super().__init__(
            bus,
            _INIT_SEQUENCE,
            **kwargs,
            set_column_command=0x15,
            set_row_command=0x75,
            single_byte_bounds=True,
            data_as_commands=True,
        )
