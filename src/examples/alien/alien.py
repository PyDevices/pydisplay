"""
alien.py
=========

.. figure:: ../_static/alien.jpg
    :align: center

    Bounce a bitmap of an alien around the display.

The alien_bitmap module was created using the :ref:`image_converter.py<image_converter>` utility.

.. literalinclude:: ../../../examples/alien/make_alien_bitmap.sh

.. note:: This example requires the following modules:

  .. hlist::
     :columns: 3

     - `st7789py`
     - `tft_config`
     - `alien_bitmap`

The alien.png PNG file is from the Erik Flowers Weather Icons available from
https://github.com/erikflowers/weather-icons and is licensed under SIL OFL 1.1
(http://scripts.sil.org/OFL).

"""

try:
    from time import ticks_ms, sleep_ms
except ImportError:
    from multimer import sleep_ms, ticks_ms


import tft_config
import tft_bitmap

palette = tft_config.palette
import alien_bitmap as alien

SPEED_X = 3
SPEED_Y = 2
TICKS = 100


def main():
    """
    Runs the main loop for the bounce animation.
    """

    tft = tft_config.config(tft_config.WIDE)
    width, height = tft.width, tft.height
    col, row = width // 2 - alien.WIDTH // 2, height // 2 - alien.HEIGHT // 2
    xd, yd = SPEED_X, SPEED_Y
    last_col, old_row = col, row

    while True:
        last = ticks_ms()
        tft.draw.fill_rect(last_col, old_row, alien.WIDTH, alien.HEIGHT, 0)
        tft_bitmap.bitmap(tft, alien, col, row)
        last_col, old_row = col, row
        col, row = col + xd, row + yd
        xd = -xd if col <= 0 or col >= width - alien.WIDTH else xd
        yd = -yd if row <= 0 or row >= height - alien.HEIGHT else yd

        if ticks_ms() - last < TICKS:
            sleep_ms(TICKS - (ticks_ms() - last))


main()
