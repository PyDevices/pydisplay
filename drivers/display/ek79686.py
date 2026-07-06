
try:
    import digitalio
except ImportError:
    pass
try:
    from epaperdisplay import EPaperDisplay
except ImportError:
    from epaperdisplay_chip import EPaperDisplay

# SPDX-FileCopyrightText: 2017 Scott Shawcroft, written for Adafruit Industries
# SPDX-FileCopyrightText: Copyright (c) 2023 Melissa LeBlanc-Williams for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
`adafruit_ek79686`
================================================================================

CircuitPython `displayio` driver for EK79686-based ePaper displays


* Author(s): Melissa LeBlanc-Williams

Implementation Notes
--------------------

**Hardware:**

* `Adafruit 2.7" Tri-Color eInk / ePaper Display with SRAM <https://www.adafruit.com/product/4098>`_

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://circuitpython.org/downloads

"""

import math


try:
    import typing

    from fourwire import FourWire
except ImportError:
    pass

__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_EK79686.git"

_START_SEQUENCE = (
    b"\x00\x01\x0f"  # LUT from OTP 176x264
    b"\x4d\x01\xaa"  # FITI cmd (???)
    b"\x87\x01\x28"
    b"\x84\x01\x00"
    b"\x83\x01\x05"
    b"\xa8\x01\xdf"
    b"\xa9\x01\x05"
    b"\xb1\x01\xe8"
    b"\xab\x01\xa1"
    b"\xb9\x01\x10"
    b"\x88\x01\x80"
    b"\x90\x01\x02"
    b"\x86\x01\x15"
    b"\x91\x01\x8d"
    b"\xaa\x01\x0f"
    b"\x04\x00"  # Power on
)

_STOP_SEQUENCE = b"\x02\x01\xff\x07\x01\xa5"  # Power off  # Deep sleep


# pylint: disable=too-few-public-methods
class EK79686(EPaperDisplay):
    """EK79686 display driver"""

    def __init__(self, bus: FourWire, **kwargs) -> None:
        start_sequence = bytearray(_START_SEQUENCE)

        width = 8 * math.ceil(kwargs["width"] / 8)
        height = 8 * math.ceil(kwargs["height"] / 8)
        if "rotation" in kwargs and kwargs["rotation"] % 180 == 0:
            width, height = height, width
            kwargs["width"] = width
            kwargs["height"] = height

        super().__init__(
            bus,
            start_sequence,
            _STOP_SEQUENCE,
            **kwargs,
            ram_width=width,
            ram_height=height,
            busy_state=False,
            write_black_ram_command=0x10,
            black_bits_inverted=False,
            color_bits_inverted=False,
            write_color_ram_command=0x13,
            refresh_display_command=0x12,
        )
