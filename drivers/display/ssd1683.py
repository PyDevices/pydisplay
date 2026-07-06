
try:
    import digitalio
except ImportError:
    pass
try:
    from epaperdisplay import EPaperDisplay
except ImportError:
    from epaperdisplay_chip import EPaperDisplay

# SPDX-FileCopyrightText: 2017 Scott Shawcroft, written for Adafruit Industries
# SPDX-FileCopyrightText: Copyright (c) 2025 Scott Shawcroft for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
`adafruit_ssd1683`
================================================================================

CircuitPython `displayio` driver for SSD1683-based ePaper displays


* Author(s): Scott Shawcroft

Implementation Notes
--------------------

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
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_SSD1683.git"

_START_SEQUENCE = (
    b"\x12\x80\x00\x32"  # soft reset and wait 50ms
    b"\x21\x00\x02\x40\x00"  # Display update control 1 & 2
    b"\x3c\x00\x01\x05"  # border waveform control
    b"\x11\x00\x01\x03"  # Ram data entry mode
    b"\x18\x00\x01\x80"  # temp control
    b"\x01\x00\x03\x00\x00\x00"  # driver output control
)

_DISPLAY_UPDATE_MODE = b"\x22\x00\x01\xf7"  # display update mode

_STOP_SEQUENCE = b"\x10\x80\x01\x01\x64"  # Deep Sleep


# pylint: disable=too-few-public-methods
class SSD1683(EPaperDisplay):
    r"""SSD1683 driver

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

    def __init__(self, bus: FourWire, custom_lut: bytes = b"", **kwargs) -> None:
        stop_sequence = bytearray(_STOP_SEQUENCE)
        try:
            bus.reset()
        except RuntimeError:
            # No reset pin defined, so no deep sleeping
            stop_sequence = b""

        load_lut = b""
        display_update_mode = bytearray(_DISPLAY_UPDATE_MODE)
        if custom_lut:
            load_lut = b"\x32" + len(custom_lut).to_bytes(2) + custom_lut
            display_update_mode[-1] = 0xC7

        start_sequence = bytearray(_START_SEQUENCE + load_lut + display_update_mode)

        width = kwargs["width"]
        height = kwargs["height"]
        if "rotation" in kwargs and kwargs["rotation"] % 180 != 90:
            width, height = height, width

        if "highlight_color" in kwargs or "grayscale" in kwargs:
            # Enable color RAM
            start_sequence[7] = 0
        if "highlight_color" in kwargs:
            # Switch refresh mode
            display_update_mode[-1] = 0xF7
        start_sequence[len(_START_SEQUENCE) - 3] = (width - 1) & 0xFF
        start_sequence[len(_START_SEQUENCE) - 2] = ((width - 1) >> 8) & 0xFF

        super().__init__(
            bus,
            start_sequence,
            stop_sequence,
            **kwargs,
            colstart=0,
            # Although the docs say ram_width is in pixels, it determines the wrong
            # number of bytes in the address. So, provide number of bytes.
            ram_width=400 // 8,
            ram_height=300,
            busy_state=True,
            write_black_ram_command=0x24,
            write_color_ram_command=0x26,
            set_column_window_command=0x44,
            set_row_window_command=0x45,
            set_current_column_command=0x4E,
            set_current_row_command=0x4F,
            refresh_display_command=0x20,
            always_toggle_chip_select=False,
            address_little_endian=True,
            two_byte_sequence_length=True,
        )
