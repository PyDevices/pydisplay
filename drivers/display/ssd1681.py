# SPDX-FileCopyrightText: 2017 Scott Shawcroft, written for Adafruit Industries
# SPDX-FileCopyrightText: Copyright (c) 2021 Melissa LeBlanc-Williams for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
`adafruit_ssd1681`
================================================================================

CircuitPython `displayio` driver for SSD1681-based ePaper displays


* Author(s): Melissa LeBlanc-Williams

Implementation Notes
--------------------

**Hardware:**

* `Adafruit 1.54" Tri-Color Display Breakout <https://www.adafruit.com/product/4868>`_

**Software and Dependencies:**

* Adafruit CircuitPython firmware (version 5+) for the supported boards:
  https://github.com/adafruit/circuitpython/releases

"""


try:
    import typing

    from fourwire import FourWire
except ImportError:
    pass

__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_SSD1681.git"

_START_SEQUENCE = (
    b"\x12\x80\x14"  # soft reset and wait 20ms
    b"\x11\x01\x03"  # Ram data entry mode
    b"\x3c\x01\x05"  # border color
    b"\x18\x01\x80"  # Temp control
    b"\x4e\x01\x00"  # ram x count
    b"\x4f\x02\x00\x00"  # ram y count
    b"\x01\x03\x00\x00\x00"  # set display size
    b"\x22\x01\xf7"  # only do full screen updates
)

# 4-gray start sequence. Uses TWO-byte command lengths (two_byte_sequence_length=True) so the
# 153-byte waveform LUT loads correctly — a single-byte length > 127 would trip displayio's
# 0x80 "delay follows" flag and corrupt the sequence. Mirrors the Good Display / GxEPD2
# GDEY0154D67 _Init_4G sequence: gate / border 0x00 / temp / RAM window / LUT only. It deliberately
# omits DISP_CTRL1 (0x21) RED-RAM enable and the VCOM/gate/source-voltage commands — those produce
# full-panel speckle on this SSD1681 panel; the custom LUT + OTP voltages are sufficient.
_GRAY4_START_SEQUENCE = (
    b"\x12\x80\x00\x14"  # soft reset and wait 20ms
    b"\x11\x00\x01\x03"  # Ram data entry mode
    b"\x3c\x00\x01\x00"  # border color (0x00 for 4-gray)
    b"\x18\x00\x01\x80"  # temp control
    b"\x4e\x00\x01\x00"  # ram x count
    b"\x4f\x00\x02\x00\x00"  # ram y count
    b"\x01\x00\x03\x00\x00\x00"  # set display size (low @ offset 28, high @ 29)
)

_STOP_SEQUENCE = b"\x10\x81\x01\x64"  # Deep Sleep


# 4-gray (grayscale) waveform LUT for the 1.54" 200x200 GDEY0154D67 / SSD1681 (#4196).
# This is the authoritative GxEPD2 `GxEPD2_154_GDEY0154D67::lut_4G` waveform with L0/L3 swapped
# to match CircuitPython's luma mapping (luma 0 -> L0 = black, luma 255 -> L3 = white). It is
# byte-identical to adafruit_ssd1680's FPC7519_LUT — the GDEY0154D67 (1.54") and GDEM029T94 (2.9")
# panels share this 4-gray waveform. DC-balance byte = 0x48.
# 153 bytes: 5 voltage-source rows (12 B each) + 12 timing groups (7 B each) + FR/XON (9 B).
GRAY4_LUT = (
    b"\x20\x48\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00"  # VS L0 (black)
    b"\x08\x48\x10\x00\x00\x00\x00\x00\x00\x00\x00\x00"  # VS L1 (dark gray)
    b"\x02\x48\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00"  # VS L2 (light gray)
    b"\x40\x48\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00"  # VS L3 (white)
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"  # VS L4 (vcom)
    b"\x0a\x19\x00\x03\x08\x00\x00"  # TP, SR, RP Group0
    b"\x14\x01\x00\x14\x01\x00\x03"  # TP, SR, RP Group1
    b"\x0a\x03\x00\x08\x19\x00\x00"  # TP, SR, RP Group2
    b"\x01\x00\x00\x00\x00\x00\x01"  # TP, SR, RP Group3
    b"\x00\x00\x00\x00\x00\x00\x00"  # TP, SR, RP Group4
    b"\x00\x00\x00\x00\x00\x00\x00"  # TP, SR, RP Group5
    b"\x00\x00\x00\x00\x00\x00\x00"  # TP, SR, RP Group6
    b"\x00\x00\x00\x00\x00\x00\x00"  # TP, SR, RP Group7
    b"\x00\x00\x00\x00\x00\x00\x00"  # TP, SR, RP Group8
    b"\x00\x00\x00\x00\x00\x00\x00"  # TP, SR, RP Group9
    b"\x00\x00\x00\x00\x00\x00\x00"  # TP, SR, RP Group10
    b"\x00\x00\x00\x00\x00\x00\x00"  # TP, SR, RP Group11
    b"\x22\x22\x22\x22\x22\x22\x00\x00\x00"  # FR, XON
)


# pylint: disable=too-few-public-methods
class SSD1681(EPaperDisplay):
    r"""SSD1681 driver

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
        * *custom_lut* (``bytes``) --
          Custom 4-gray waveform LUT (e.g. ``GRAY4_LUT``). Pass with ``grayscale=True``.
    """

    def __init__(self, bus: FourWire, custom_lut: bytes = b"", **kwargs) -> None:
        width = kwargs["width"]
        height = kwargs["height"]
        if "rotation" in kwargs and kwargs["rotation"] % 180 != 0:
            width, height = height, width

        if custom_lut:
            # 4-gray: load the custom LUT and switch to LUT-based (0xC7) update. The start
            # sequence already matches GxEPD2's _Init_4G — no 0x21 RED-RAM enable and no
            # VCOM/gate/source-voltage commands (those speckle this SSD1681 panel).
            load_lut = b"\x32" + len(custom_lut).to_bytes(2, "big") + custom_lut
            update_mode = b"\x22\x00\x01\xc7"
            start_sequence = bytearray(_GRAY4_START_SEQUENCE + load_lut + update_mode)
            start_sequence[28] = (width - 1) & 0xFF
            start_sequence[29] = ((width - 1) >> 8) & 0xFF
            two_byte_len = True
        else:
            start_sequence = bytearray(_START_SEQUENCE)
            start_sequence[21] = (width - 1) & 0xFF
            start_sequence[22] = ((width >> 8) - 1) & 0xFF
            two_byte_len = False

        # RAM is actually only 200 bits high but we use 296 to match the 9 bits
        # (and therefore two bytes) used to address height.
        super().__init__(
            bus,
            start_sequence,
            _STOP_SEQUENCE,
            **kwargs,
            ram_width=200,
            ram_height=296,
            busy_state=True,
            write_black_ram_command=0x24,
            write_color_ram_command=0x26,
            black_bits_inverted=False,
            set_column_window_command=0x44,
            set_row_window_command=0x45,
            set_current_column_command=0x4E,
            set_current_row_command=0x4F,
            refresh_display_command=0x20,
            always_toggle_chip_select=True,
            address_little_endian=True,
            two_byte_sequence_length=two_byte_len,
        )
