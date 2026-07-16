# deps: palettes
"""
boxlines.py
===========

.. figure:: ../_static/boxlines.jpg
    :align: center

    Test for lines and rectangles.

Draws lines and rectangles in random colors at random locations on the display.

.. note:: This example requires the following modules:

  .. hlist::
    :columns: 3

    - `st7789py`
    - `tft_config`

"""

from board_config import runtime

from random import getrandbits

import tft_config

palette = tft_config.palette


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


def _setup():
    tft = tft_config.config(tft_config.WIDE)

    def poll():
        color = palette.color565(getrandbits(8), getrandbits(8), getrandbits(8))

        tft.draw.line(
            randint(0, tft.width),
            randint(0, tft.height),
            randint(0, tft.width),
            randint(0, tft.height),
            color,
        )

        width = randint(0, tft.width // 2)
        height = randint(0, tft.height // 2)
        col = randint(0, tft.width - width)
        row = randint(0, tft.height - height)
        tft.draw.fill_rect(
            col,
            row,
            width,
            height,
            palette.color565(getrandbits(8), getrandbits(8), getrandbits(8)),
        )
        tft.show()
        return False

    return poll


poll = _setup()


def _tick(_=None):
    poll()


runtime.on_tick(_tick, period=1, async_=runtime.timer_async)
runtime.run_forever()
