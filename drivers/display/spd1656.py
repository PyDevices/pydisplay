# SPDX-FileCopyrightText: 2017 Scott Shawcroft, written for Adafruit Industries
# SPDX-FileCopyrightText: Copyright (c) 2023 Scott Shawcroft for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
`adafruit_spd1656`
================================================================================

Driver for SPD1656 driven ACeP (7-color) e-paper displays


* Author(s): Scott Shawcroft

Implementation Notes
--------------------

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://circuitpython.org/downloads

"""

import struct

import epaperdisplay

__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_SPD1656.git"

_START_SEQUENCE = (
    b"\x01\x04\x37\x00\x23\x23"  # power setting
    b"\x00\x02\xef\x08"  # panel setting (PSR)
    b"\x03\x01\x00"  # PFS
    b"\x06\x03\xc7\xc7\x1d"  # booster
    b"\x30\x01\x3c"  # PLL setting
    b"\x41\x01\x00"  # TSE
    b"\x50\x01\x37"  # vcom and data interval setting
    b"\x60\x01\x22"  # tcon setting
    b"\x61\x04\x02\x58\x01\xc0"  # tres
    b"\xe3\x01\xaa"  # PWS
    b"\x04\x80\xc8"  # power on and wait 10 ms
)

_STOP_SEQUENCE = b"\x02\x01\x00\x07\x01\xa5"  # Power off then deep sleep

# Datasheet is here: https://www.waveshare.com/w/upload/b/bf/SPD1656_1.1.pdf


class SPD1656(epaperdisplay.EPaperDisplay):
    r"""SPD1656 display driver

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

    def __init__(self, bus, **kwargs):
        width = kwargs["width"]
        height = kwargs["height"]
        if "rotation" in kwargs and kwargs["rotation"] % 180 != 0:
            width, height = height, width

        start_sequence = bytearray(_START_SEQUENCE)

        if height <= 320:
            resa = 0
        else:
            resa = 1

        if width == 640:
            res0 = 0
        else:
            res0 = 1

        if height == 448:
            res1 = 1
        else:
            res1 = 0

        # Patch PSR's display resolution setting
        start_sequence[8] |= res1 << 7 | res0 << 6 | resa << 5

        # Patch tres
        struct.pack_into(">HH", start_sequence, 32, width, height)

        # This assumes the chip is used for an ACeP display even though the
        # datasheet is documented as 4 grays and 4 reds.
        super().__init__(
            bus,
            start_sequence,
            _STOP_SEQUENCE,
            **kwargs,
            ram_width=640,
            ram_height=480,
            start_up_time=1,
            busy_state=False,
            write_black_ram_command=0x10,
            refresh_display_command=0x12,
            advanced_color_epaper=True,
        )
