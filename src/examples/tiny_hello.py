from board_config import broker
from eventsys import poll_quit_discarding_others
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

try:
    import pydisplay_test_mode

    _iterations = 4 if pydisplay_test_mode.ENABLED else 128
except ImportError:
    _iterations = 128

palette = tft_config.palette
import vga1_8x8 as font

tft = tft_config.config(tft_config.WIDE)


def _quit_requested():
    return poll_quit_discarding_others(broker)


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
        if _quit_requested():
            return
        for _ in range(100):
            if _quit_requested():
                return
            sleep_ms(10)

    while True:
        if _quit_requested():
            return
        for rotation in range(4):
            if _quit_requested():
                return
            tft.rotation = rotation
            tft.draw.fill(0)
            tft.show()
            if _quit_requested():
                return
            col_max = tft.width - font.WIDTH * 6
            row_max = tft.height - font.HEIGHT

            for _ in range(_iterations):
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
                if _quit_requested():
                    return


main()
