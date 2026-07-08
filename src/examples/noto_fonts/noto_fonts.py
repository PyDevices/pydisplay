# multimer types: all
"""
noto_fonts.py
=============

.. figure:: ../_static/noto_fonts.jpg
    :align: center

    Test for TrueType write_font_converter.

Writes the names of three Noto fonts centered on the display using the font.
The fonts were converted from True Type fonts using the
:ref:`write_font_converter.py<write_font_converter>` utility.

.. note:: This example requires the following modules:

  .. hlist::
    :columns: 3

    - `st7789py`
    - `tft_config`
    - `NotoSans_32`
    - `NotoSerif_32`
    - `NotoSansMono_32`

"""

import sys

import tft_config
from board_config import runtime
from multimer import Timer

palette = tft_config.palette
sys.path.insert(0, __file__.replace("\\", "/").rsplit("/", 1)[0])
import NotoSans_32 as noto_sans
import NotoSerif_32 as noto_serif
import NotoSansMono_32 as noto_mono
import tft_write


def main():
    """main"""

    def center(font, string, row, color=palette.WHITE):
        """
        Centers the given string horizontally on the screen at the specified row.

        Args:
            font: The font to use for rendering the string.
            string: The string to be centered.
            row: The row where the string will be displayed.
            color: The color of the string (default: palette.WHITE).

        Returns:
            None
        """

        screen = tft.width  # get screen width
        width = tft_write.write_width(font, string)  # get the width of the string
        col = tft.width // 2 - width // 2 if width and width < screen else 0
        tft_write.write(tft, font, string, col, row, color)  # and write the string

    # initialize the display
    tft = tft_config.config(tft_config.WIDE)
    row = 16

    # center the name of the first font, using the font
    center(noto_sans, "NotoSans", row, palette.RED)
    row += noto_sans.HEIGHT

    # center the name of the second font, using the font
    center(noto_serif, "NotoSerif", row, palette.GREEN)
    row += noto_serif.HEIGHT

    # center the name of the third font, using the font
    center(noto_mono, "NotoSansMono", row, palette.BLUE)
    row += noto_mono.HEIGHT

    tft.show()
    runtime.poll()


main()
