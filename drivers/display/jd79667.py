
try:
    import digitalio
except ImportError:
    pass
try:
    from epaperdisplay import EPaperDisplay
except ImportError:
    from epaperdisplay_chip import EPaperDisplay

# SPDX-FileCopyrightText: Copyright (c) 2025 Scott Shawcroft for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
`adafruit_jd79667`
================================================================================

CircuitPython `displayio` driver for JD79667-based ePaper displays


* Author(s): Scott Shawcroft

Implementation Notes
--------------------

**Hardware:**

* JD79667-based 4-color ePaper displays (128x250 resolution) - Black, White, Red, Yellow

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
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_JD79667.git"

# JD79667 Command definitions
_JD79667_PANEL_SETTING = 0x00
_JD79667_POWER_SETTING = 0x01
_JD79667_POWER_OFF = 0x02
_JD79667_POWER_ON = 0x04
_JD79667_BOOSTER_SOFTSTART = 0x06
_JD79667_DEEP_SLEEP = 0x07
_JD79667_DATA_START_XMIT = 0x10
_JD79667_DISPLAY_REFRESH = 0x12
_JD79667_CDI = 0x50
_JD79667_PLL_CONTROL = 0x60
_JD79667_RESOLUTION = 0x61

_START_SEQUENCE = (
    b"\x4d\x01\x78"  # Set register 0x4D to 0x78
    b"\x00\x02\x8f\x29"  # Panel setting
    b"\x01\x02\x07\x00"  # Power setting
    b"\x03\x03\x10\x54\x44"  # Power offset
    b"\x06\x07\x05\x00\x3f\x0a\x25\x12\x1a"  # Booster soft start
    b"\x50\x01\x37"  # CDI
    b"\x60\x02\x02\x02"  # TCON
    b"\x61\x04\x00\xb4\x01\x80"  # Resolution (0, 180, 0, 384)
    b"\xe7\x01\x1c"  # Additional config register
    b"\xe3\x01\x22"  # Additional config register
    b"\xb4\x01\xd0"  # Additional config register
    b"\xb5\x01\x03"  # Additional config register
    b"\xe9\x01\x01"  # Additional config register
    b"\x30\x01\x08"  # PLL Control
    b"\x04\x00"  # Power on and wait
)

_STOP_SEQUENCE = (
    b"\x02\x80\x00"  # Power off and wait
    b"\x07\x01\xa5"  # Deep sleep
)

_REFRESH_SEQUENCE = b"\x12\x01\x00"  # Display refresh

_SUPPORTED_RESOLUTIONS = ((200, 384), (184, 384), (168, 384), (200, 200))


# pylint: disable=too-few-public-methods
class JD79667(EPaperDisplay):
    r"""JD79667 driver

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
        stop_sequence = bytearray(_STOP_SEQUENCE)
        try:
            bus.reset()
        except RuntimeError:
            # No reset pin defined, so no deep sleeping
            stop_sequence = b""

        start_sequence = bytearray(_START_SEQUENCE)

        width = kwargs.get("width", 200)
        height = kwargs.get("height", 384)
        if "rotation" in kwargs and kwargs["rotation"] % 180 != 0:
            width, height = height, width

        if (width, height) not in _SUPPORTED_RESOLUTIONS:
            raise ValueError("Unsupported resolution")

        start_sequence[5] |= _SUPPORTED_RESOLUTIONS.index((width, height)) << 6

        # Update resolution in start sequence (bytes at position for resolution command)
        # Find the resolution command in the sequence and update it
        res_pos = start_sequence.find(b"\x61\x04")
        if res_pos != -1:
            if width % 4 != 0:
                width += 4 - width % 4
            start_sequence[res_pos + 2] = (width >> 8) & 0xFF
            start_sequence[res_pos + 3] = width & 0xFF
            start_sequence[res_pos + 4] = (height >> 8) & 0xFF
            start_sequence[res_pos + 5] = height & 0xFF

        super().__init__(
            bus,
            start_sequence,
            stop_sequence,
            **kwargs,
            ram_width=200,
            ram_height=384,
            busy_state=False,
            write_black_ram_command=_JD79667_DATA_START_XMIT,
            write_color_ram_command=None,  # JD79667 uses single RAM with 2-bit pixels
            refresh_display_command=_REFRESH_SEQUENCE,
            always_toggle_chip_select=True,
            address_little_endian=False,
        )
