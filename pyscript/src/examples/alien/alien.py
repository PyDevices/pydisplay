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
from multimer import Timer
from multimer.loop import run_forever

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

    def poll():
        tft.draw.fill_rect(st["last_col"], st["old_row"], alien.WIDTH, alien.HEIGHT, 0)
        tft_bitmap.bitmap(tft, alien, st["col"], st["row"])
        tft.show()
        elist = runtime.poll() if runtime else []
        if runtime.quit_requested if runtime else False:
            return True
        if any(e.type == runtime.events.QUIT for e in elist):
            return True
        st["last_col"], st["old_row"] = st["col"], st["row"]
        st["col"], st["row"] = st["col"] + st["xd"], st["row"] + st["yd"]
        st["xd"] = -st["xd"] if st["col"] <= 0 or st["col"] >= width - alien.WIDTH else st["xd"]
        st["yd"] = -st["yd"] if st["row"] <= 0 or st["row"] >= height - alien.HEIGHT else st["yd"]
        return False

    # run_forever blocks on desktop/MCU but yields to the event loop on
    # PyScript/Jupyter (runtime.timer_async); delay_ms sets the frame pace.
    run_forever(poll, delay_ms=TICKS)


main()
