# multimer types: all
"""
tiny_hello.py
=============

.. figure:: ../_static/tiny_hello.jpg
    :align: center

    Test text_font_converter on small displays.

Writes "Hello!" in a tiny font in random colors at random locations on the Display.

.. note:: This example requires the following modules:

  .. hlist::
    :columns: 3

    - `st7789py`
    - `tft_config`
    - `vga1_8x8`

"""

from random import getrandbits

from multimer import sleep_ms
import tft_text
import tft_config

palette = tft_config.palette
import vga1_8x8 as font

tft = tft_config.config(tft_config.WIDE)


def randint(a, b):
    span = b - a + 1
    if span <= 1:
        return a
    bits = 0
    n = span - 1
    while n:
        bits += 1
        n >>= 1
    return a + getrandbits(bits) % span


def center(text, fg=palette.WHITE, bg=palette.BLACK):
    """
    Centers the given text on the display.
    """
    length = len(text)
    tft_text.text(
        tft,
        font,
        text,
        tft.width // 2 - length // 2 * font.WIDTH,
        tft.height // 2 - font.HEIGHT,
        fg,
        bg,
    )


def main():
    """
    The big show!
    """
    for color in [palette.RED, palette.GREEN, palette.BLUE]:
        tft.draw.fill(color)
        tft.draw.rect(0, 0, tft.width, tft.height, palette.WHITE)
        center("Hello!", palette.WHITE, color)
        tft.show()
        sleep_ms(1000)

    while True:
        for rotation in range(4):
            tft.rotation = rotation
            tft.draw.fill(0)
            tft.show()
            col_max = tft.width - font.WIDTH * 6
            row_max = tft.height - font.HEIGHT

            for _ in range(128):
                tft_text.text(
                    tft,
                    font,
                    "Hello!",
                    randint(0, col_max),
                    randint(0, row_max),
                    palette.color565(
                        getrandbits(8),
                        getrandbits(8),
                        getrandbits(8),
                    ),
                    palette.color565(
                        getrandbits(8),
                        getrandbits(8),
                        getrandbits(8),
                    ),
                )
                tft.show()


main()
