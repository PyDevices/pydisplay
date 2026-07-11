from board_config import runtime
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

from random import getrandbits

import tft_config
from multimer.loop import run_forever

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
        if runtime:
            runtime.poll()
            if runtime.quit_requested:
                return True
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


# run_forever blocks on desktop/MCU but yields to the event loop on PyScript
# and Jupyter (runtime.timer_async), so the browser main thread stays live.
run_forever(_setup(), delay_ms=0)
