# SPDX-FileCopyrightText: 2017 Scott Shawcroft, written for Adafruit Industries
# SPDX-FileCopyrightText: Copyright (c) 2023 Scott Shawcroft for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
`adafruit_acep7in`
================================================================================

Driver for 7.3" 7-color (aka ACeP) epaper display


* Author(s): Scott Shawcroft

Implementation Notes
--------------------

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://circuitpython.org/downloads

"""


from fourwire import FourWire

__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_ACeP7In.git"

_START_SEQUENCE = (
    b"\xaa\x06\x49\x55\x20\x08\x09\x18"  # CMDH
    b"\x01\x06\x3f\x00\x32\x2a\x0e\x2a"  # power setting PWRR
    b"\x00\x02\x5f\x69"  # panel setting (PSR)
    b"\x03\x04\x00\x54\x00\x44"  # POFS
    b"\x05\x04\x40\x1f\x1f\x2c"  # booster BTST1
    b"\x06\x04\x6f\x1f\x16\x25"  # booster BTST2
    b"\x08\x04\x6f\x1f\x1f\x22"  # booster BTST3
    b"\x13\x02\x00\x04"  # IPC
    b"\x30\x01\x02"  # PLL setting
    b"\x41\x01\x00"  # TSE
    b"\x50\x01\x3f"  # vcom and data interval setting
    b"\x60\x02\x02\x00"  # tcon setting
    b"\x61\x04\x03\x20\x01\xe0"  # tres
    b"\x82\x01\x1e"  # vdcs
    b"\x84\x01\x00"  # t_vdcs
    b"\x86\x01\x00"  # agid
    b"\xe3\x01\x2f"  # PWS
    b"\xe0\x01\x00"  # ccset
    b"\xe6\x01\x00"  # tsset
    b"\x04\x80\xc8"  # power on and wait 10 ms
)

_STOP_SEQUENCE = b"\x02\x01\x00"  # Power off only


# pylint: disable=too-few-public-methods
class ACeP7In(EPaperDisplay):
    r"""Display driver for 7" ACeP epaper display. Driver IC name is unknown.

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

    def __init__(self, bus: FourWire, **kwargs):
        width = kwargs["width"]
        height = kwargs["height"]
        if "rotation" in kwargs and kwargs["rotation"] % 180 != 0:
            width, height = height, width

        super().__init__(
            bus,
            _START_SEQUENCE,
            _STOP_SEQUENCE,
            **kwargs,
            ram_width=800,
            ram_height=480,
            start_up_time=1,
            busy_state=False,
            write_black_ram_command=0x10,
            refresh_display_command=b"\x12\x01\x00",
            advanced_color_epaper=True,
        )
