# multimer types: all
# pyscript files: fonts.py
"""
fonts.py
========

.. figure:: ../_static/fonts.jpg
    :align: center

    Test text_font_converter.py

Pages through all characters of four fonts on the Display.
https://www.youtube.com/watch?v=2cnAhEucPD4

.. note:: This example requires the following modules:

  .. hlist::
    :columns: 3

    - `st7789py`
    - `tft_config`
    - `vga2_8x8`
    - `vga2_8x16`
    - `vga2_bold_16x16`
    - `vga2_bold_16x32`

"""

from multimer import sleep_ms

import tft_config
import tft_text
import vga2_8x8 as font1
import vga2_8x16 as font2
import vga2_bold_16x16 as font3
import vga2_bold_16x32 as font4

palette = tft_config.palette


def main():
    tft = tft_config.config(tft_config.WIDE)
    tft.vscrdef(0, tft.height, 0)

    while True:
        for font in (font1, font2, font3, font4):
            tft.draw.fill(palette.BLUE)
            tft.show()
            line = 0
            col = 0

            for char in range(font.FIRST, font.LAST):
                tft_text.text(tft, font, chr(char), col, line, palette.WHITE, palette.BLUE)
                tft.show()
                col += font.WIDTH
                if col > tft.width - font.WIDTH:
                    col = 0
                    line += font.HEIGHT

                    if line > tft.height - font.HEIGHT:
                        sleep_ms(3000)
                        tft.draw.fill(palette.BLUE)
                        tft.show()
                        line = 0
                        col = 0

            sleep_ms(3000)


main()
