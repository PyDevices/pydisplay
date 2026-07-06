try:
    from displaysys.busdisplay import BusDisplay
except ImportError:
    from busdisplay import BusDisplay

# SPDX-FileCopyrightText: 2019 Melissa LeBlanc-Williams for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_displayio_ssd1305`
================================================================================

DisplayIO driver for SSD1305 monochrome displays


* Author(s): Melissa LeBlanc-Williams

Implementation Notes
--------------------

**Hardware:**

* `Monochrome 1.54" 128x64 OLED Graphic Display Module Kit <https://www.adafruit.com/product/2720>`_
* `Monochrome 2.42" 128x64 OLED Graphic Display Module Kit <https://www.adafruit.com/product/2719>`_
* `Monochrome 2.3" 128x32 OLED Graphic Display Module Kit <https://www.adafruit.com/product/2675>`_

**Software and Dependencies:**

* Adafruit CircuitPython (version 5+) firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

"""

# imports

try:
    from typing import Union

    from fourwire import FourWire
    from i2cdisplaybus import I2CDisplayBus
except ImportError:
    pass




_INIT_SEQUENCE = (
    b"\xae\x00"  # DISPLAY_OFF
    b"\xd5\x01\x80"  # SET_DISP_CLK_DIV
    b"\xa1\x00"  # Column 127 is segment 0
    b"\xa8\x01\x3f"  # Mux ratio is 1/64
    b"\xad\x01\x8e"  # Set Master Configuration
    b"\xd8\x01\x05"  # Set Area Color Mode On/Off & Low Power Display Mode
    b"\x20\x01\x00"  # Set memory addressing to horizontal mode.
    b"\x40\x01\x2e"  # SET_DISP_START_LINE ADD
    b"\xc8\x00"  # Set COM Output Scan Direction 64 to 1
    b"\xda\x01\x12"  # Set com configuration
    b"\x91\x04\x3f\x3f\x3f\x3f"  # Current drive pulse width of BANK0, Color A, Band C.
    b"\xd9\x01\xd2"  # Set pre-charge period orig: 0xd9, 0x22 if self.external_vcc else 0xf1,
    b"\xdb\x01\x34"  # Set vcom configuration 0xdb, 0x30, $ 0.83* Vcc
    b"\xa6\x00"  # Normal display
    b"\xa4\x00"  # output follows RAM contents  SET_ENTIRE_ON
    b"\x8d\x01\x14"  # Enable charge pump
    b"\xaf\x00\x00"  # DISPLAY_ON
)


# pylint: disable=too-few-public-methods
class SSD1305(BusDisplay):
    """
    SSD1305 driver

    :param int width: The width of the display
    :param int height: The height of the display
    :param int rotation: The rotation of the display in degrees. Default is 0.
        One of (0, 90, 180, 270)
    """

    def __init__(self, bus: Union[FourWire, I2CDisplayBus], **kwargs) -> None:
        colstart = 0
        # Patch the init sequence for 32 pixel high displays.
        init_sequence = bytearray(_INIT_SEQUENCE)

        height = kwargs["height"]
        if "rotation" in kwargs and kwargs["rotation"] % 180 != 0:
            height = kwargs["width"]
        init_sequence[9] = height - 1  # patch mux ratio

        if kwargs["height"] == 32:
            colstart = 4
        super().__init__(
            bus,
            init_sequence,
            **kwargs,
            color_depth=1,
            grayscale=True,
            pixels_in_byte_share_row=False,
            set_column_command=0x21,
            set_row_command=0x22,
            data_as_commands=True,
            brightness_command=0x81,
            single_byte_bounds=True,
            colstart=colstart,
        )
