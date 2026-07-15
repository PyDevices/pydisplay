# pyscript mip: palettes
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

from board_config import runtime

import tft_config
import tft_bitmap

palette = tft_config.palette
import sys

sys.path.insert(0, __file__.replace("\\", "/").rsplit("/", 1)[0])
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
    st = {
        "col": width // 2 - alien.WIDTH // 2,
        "row": height // 2 - alien.HEIGHT // 2,
        "xd": SPEED_X,
        "yd": SPEED_Y,
    }
    st["last_col"], st["old_row"] = st["col"], st["row"]

    def _tick(_=None):
        # Do not call runtime.poll() from on_tick: sync backends (librt/win32)
        # re-enter the timer path and hang. Auto-service handles QUIT.
        if runtime.quit_requested if runtime else False:
            return
        tft.draw.fill_rect(st["last_col"], st["old_row"], alien.WIDTH, alien.HEIGHT, 0)
        tft_bitmap.bitmap(tft, alien, st["col"], st["row"])
        tft.show()
        st["last_col"], st["old_row"] = st["col"], st["row"]
        st["col"], st["row"] = st["col"] + st["xd"], st["row"] + st["yd"]
        st["xd"] = -st["xd"] if st["col"] <= 0 or st["col"] >= width - alien.WIDTH else st["xd"]
        st["yd"] = -st["yd"] if st["row"] <= 0 or st["row"] >= height - alien.HEIGHT else st["yd"]

    runtime.on_tick(_tick, period=10, async_=runtime.timer_async)
    runtime.run_forever()
main()
