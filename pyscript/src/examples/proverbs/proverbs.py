"""
proverbs.py
===========

.. figure:: ../_static/proverbs.jpg
    :align: center

    Test for TrueType write_font_converter.

Displays what I hope are chinese proverbs in simplified chinese to test UTF-8 font support.
The fonts were converted from True Type fonts using the
:ref:`write_font_converter.py<write_font_converter>` utility.

.. literalinclude:: ../../../examples/proverbs/make_proverbs_fonts.sh


.. note:: This example requires the following modules:

  .. hlist::
    :columns: 3

    - `st7789py`
    - `tft_config`
    - `proverbs_20`
    - `proverbs_30`

"""

import sys

import tft_write
import tft_config
from board_config import runtime
from multimer import Timer
from multimer.loop import run_forever

palette = tft_config.palette
sys.path.insert(0, __file__.replace("\\", "/").rsplit("/", 1)[0])
import proverbs_20 as font20
import proverbs_30 as font30


tft = tft_config.config(tft_config.WIDE)


def color_wheel(WheelPos):
    """returns a 565 color from the given position of the color wheel"""
    WheelPos = (255 - WheelPos) % 255

    if WheelPos < 85:
        return palette.color565(255 - WheelPos * 3, 0, WheelPos * 3)

    if WheelPos < 170:
        WheelPos -= 85
        return palette.color565(0, WheelPos * 3, 255 - WheelPos * 3)

    WheelPos -= 170
    return palette.color565(WheelPos * 3, 255 - WheelPos * 3, 0)


def main():
    proverbs = [
        "万事起头难",
        "熟能生巧",
        "冰冻三尺，非一日之寒",
        "三个臭皮匠，胜过诸葛亮",
        "今日事，今日毕",
        "师父领进门，修行在个人",
        "一口吃不成胖子",
        "欲速则不达",
        "百闻不如一见",
        "不入虎穴，焉得虎子",
    ]

    font = font20 if tft.width < 239 else font30
    line_height = font.HEIGHT + 8
    half_height = tft.height // 2
    half_width = tft.width // 2
    st = {"index": 0, "wheel": 0}

    def poll():
        proverb = proverbs[st["index"]]
        proverb_lines = proverb.split("，")
        half_lines_height = len(proverb_lines) * line_height // 2

        tft.draw.fill(palette.BLACK)

        for count, proverb_line in enumerate(proverb_lines):
            half_length = tft_write.write_width(font, proverb_line) // 2

            tft_write.write(
                tft,
                font,
                proverb_line,
                half_width - half_length,
                half_height - half_lines_height + count * line_height,
                color_wheel(st["wheel"]),
            )

        st["wheel"] = (st["wheel"] + 5) % 256

        tft.show()
        elist = runtime.poll() if runtime else []
        if runtime.quit_requested if runtime else False:
            return True
        if any(e.type == runtime.events.QUIT for e in elist):
            return True
        st["index"] = (st["index"] + 1) % len(proverbs)
        return False

    # run_forever blocks on desktop/MCU but yields to the event loop on
    # PyScript/Jupyter (runtime.timer_async); delay_ms pauses between proverbs.
    run_forever(poll, delay_ms=5000)


main()
