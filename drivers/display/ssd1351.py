try:
    from displaysys.busdisplay import BusDisplay
except ImportError:
    from busdisplay import BusDisplay

# SPDX-FileCopyrightText: 2019 Melissa LeBlanc-Williams for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_ssd1351`
================================================================================

displayio Driver for SSD1351 Displays


* Author(s): Melissa LeBlanc-Williams

Implementation Notes
--------------------

**Hardware:**

* OLED Breakout Board - 16-bit Color 1.5" w/microSD holder:
  https://www.adafruit.com/product/1431
* OLED Breakout Board - 16-bit Color 1.27" w/microSD holder:
  https://www.adafruit.com/product/1673

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

"""

import busdisplay

try:
    import typing

    import fourwire
except ImportError:
    pass




_INIT_SEQUENCE = (
    b"\xfd\x01\x12"  # COMMAND_LOCK Unlock IC MCU
    b"\xfd\x01\xb1"  # COMMAND_LOCK
    b"\xae\x00"  # DISPLAY_OFF
    b"\xb2\x03\xa4\x00\x00"  # DISPLAY_ENHANCEMENT
    b"\xb3\x01\xf0"  # CLOCK_DIV
    b"\xca\x01\x7f"  # MUX_RATIO
    b"\xa2\x01\x00"  # DISPLAY_OFFSET
    b"\xb5\x01\x00"  # SET_GPIO
    b"\xab\x01\x01"  # FUNCTION_SELECT
    b"\xb1\x01\x32"  # PRECHARGE
    b"\xbe\x01\x05"  # VCOMH
    b"\xa6\x00"  # NORMAL_DISPLAY
    b"\xc1\x03\xc8\x80\xc8"  # CONTRAST_ABC (RGB)
    b"\xc7\x01\x0f"  # CONTRAST_MASTER
    b"\xb4\x03\xa0\xb5\x55"  # SET_VSL Set segment low volt
    b"\xb6\x01\x01"  # PRECHARGE2
    b"\xa0\x01\x26"  # Set Color Mode
    b"\xaf\x00"  # DISPLAY_ON
)


class SSD1351(busdisplay.BusDisplay):
    """SSD1351 driver"""

    def __init__(self, bus: fourwire.FourWire, **kwargs) -> None:
        super().__init__(
            bus,
            _INIT_SEQUENCE,
            **kwargs,
            set_column_command=0x15,
            set_row_command=0x75,
            write_ram_command=0x5C,
            single_byte_bounds=True,
        )
