
try:
    import digitalio
except ImportError:
    pass
try:
    from epaperdisplay import EPaperDisplay
except ImportError:
    from epaperdisplay_chip import EPaperDisplay

# SPDX-FileCopyrightText: 2017 Scott Shawcroft, written for Adafruit Industries
# SPDX-FileCopyrightText: Copyright (c) 2021 Melissa LeBlanc-Williams for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
`adafruit_uc8151d`
================================================================================

CircuitPython `displayio` driver for US8151D-based ePaper displays


* Author(s): Melissa LeBlanc-Williams

Implementation Notes
--------------------

**Hardware:**

* `Adafruit Flexible 2.9" Black and White <https://www.adafruit.com/product/4262>`_
* `Adafruit Tri-Color 2.9" <https://www.adafruit.com/product/1028>`_

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

"""


try:
    import typing

    from fourwire import FourWire
except ImportError:
    pass


__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_UC8151D.git"

_START_SEQUENCE = (
    # b"\x01\x05\x03\x00\x2b\x2b\x09"  # power setting
    # b"\x06\x03\x17\x17\x17"  # booster soft start
    b"\x04\x80\xc8"  # power on and wait 200 ms
    b"\x00\x01\x1f"  # panel setting. Further filled in below.
    b"\x50\x01\x97"  # CDI setting
)

_COLOR_START_SEQUENCE = (
    b"\x04\x80\xc8"  # power on and wait 200 ms
    b"\x00\x02\x0f\x89"  # panel setting. Further filled in below.
    b"\x61\x03\x80\x01\x28"  # Set Display Resolution
    b"\x50\x01\x77"  # CDI setting
)

_GRAYSCALE_START_SEQUENCE = (
    b"\x04\x80\xc8"  # Power on
    b"\x00\x01\xbf"  # Panel setting
    b"\x50\x01\x97"  # CDI setting
    # Common voltage
    b"\x20\x2a"
    b"\x00\x0a\x00\x00\x00\x01"
    b"\x60\x14\x14\x00\x00\x01"
    b"\x00\x14\x00\x00\x00\x01"
    b"\x00\x13\x0a\x01\x00\x01"
    b"\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00"
    # White to White
    b"\x21\x2a"
    b"\x40\x0a\x00\x00\x00\x01"
    b"\x90\x14\x14\x00\x00\x01"
    b"\x10\x14\x0a\x00\x00\x01"
    b"\xa0\x13\x01\x00\x00\x01"
    b"\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00"
    # Black to White
    b"\x22\x2a"
    b"\x40\x0a\x00\x00\x00\x01"
    b"\x90\x14\x14\x00\x00\x01"
    b"\x00\x14\x0a\x00\x00\x01"
    b"\x99\x0b\x04\x04\x01\x01"
    b"\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00"
    # White to Black
    b"\x23\x2a"
    b"\x40\x0a\x00\x00\x00\x01"
    b"\x90\x14\x14\x00\x00\x01"
    b"\x00\x14\x0a\x00\x00\x01"
    b"\x99\x0c\x01\x03\x04\x01"
    b"\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00"
    # Black to Black
    b"\x24\x2a"
    b"\x80\x0a\x00\x00\x00\x01"
    b"\x90\x14\x14\x00\x00\x01"
    b"\x20\x14\x0a\x00\x00\x01"
    b"\x50\x13\x01\x00\x00\x01"
    b"\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00"
)

_STOP_SEQUENCE = b"\x50\x01\xf7\x07\x01\xa5"  # CDI setting  # Deep Sleep


# pylint: disable=too-few-public-methods
class UC8151D(EPaperDisplay):
    r"""UC8151D driver

    :param bus: The data bus the display is on
    :param \**kwargs:
        See below

    :Keyword Arguments:
        * *width* (``int``) --
          Display width
        * *height* (``int``) --
          Display height
        * *rotation* (``int``) --
          Display rotation
    """

    def __init__(self, bus: FourWire, **kwargs) -> None:
        color_bits_inverted = kwargs.pop("color_bits_inverted", False)
        write_color_ram_command = 0x10
        write_black_ram_command = 0x13
        if kwargs.get("grayscale", False):
            start_sequence = bytearray(_GRAYSCALE_START_SEQUENCE)
        elif kwargs.get("highlight_color", False):
            write_color_ram_command = 0x13
            write_black_ram_command = 0x10
            color_bits_inverted = kwargs.pop("color_bits_inverted", True)
            start_sequence = bytearray(_COLOR_START_SEQUENCE)
        else:
            start_sequence = bytearray(_START_SEQUENCE)
        width = kwargs["width"]
        height = kwargs["height"]
        if "rotation" in kwargs and kwargs["rotation"] % 180 != 0:
            width, height = height, width

        super().__init__(
            bus,
            start_sequence,
            _STOP_SEQUENCE,
            **kwargs,
            ram_width=128,
            ram_height=296,
            busy_state=False,
            write_black_ram_command=write_black_ram_command,
            write_color_ram_command=write_color_ram_command,
            color_bits_inverted=color_bits_inverted,
            refresh_display_command=0x12,
        )
