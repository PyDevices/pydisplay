from board_config import runtime
# pyscript gallery: all
"""
scroll.py
=========

.. figure:: ../_static/scroll.jpg
    :align: center

    Test for hardware scrolling.

Smoothly scrolls all font characters up the screen.
Only works with fonts with heights that are even multiples of the screen height,
(i.e. 8 or 16 pixels high)

.. note:: This example requires the following modules:

  .. hlist::
    :columns: 3

    - `st7789py`
    - `tft_config`
    - `vga2_bold_16x16`

"""

from multimer import sleep_ms
import tft_text
import tft_config

palette = tft_config.palette
import vga2_bold_16x16 as font


def main():
    """main"""
    tft = tft_config.config(tft_config.SCROLL)
    last_line = tft.height - font.HEIGHT
    tfa = tft_config.TFA  # top free area when scrolling
    bfa = tft_config.BFA  # bottom free area when scrolling
    tft.vscrdef(tfa, tft.height - tfa - bfa, bfa)

    tft.draw.fill(palette.BLUE)
    tft.show()
    scroll = 0
    character = 0
    col = tft.width // 2 - 5 * font.WIDTH // 2

    while True:
        if runtime is not None:
            runtime.poll()
        tft.draw.fill_rect(0, scroll, tft.width, 1, palette.BLUE)

        if scroll % font.HEIGHT == 0:
            tft_text.text(
                tft,
                font,
                f"x{character:02x} {chr(character)}",
                col,
                (scroll + last_line) % tft.height,
                palette.WHITE,
                palette.BLUE,
            )

            character = character + 1 if character < 256 else 0

        tft.vscsad(scroll + tfa)
        tft.show()
        scroll += 1

        if scroll == tft.height:
            scroll = 0

        if runtime.quit_requested if runtime else False:
            break
        sleep_ms(10)


main()
