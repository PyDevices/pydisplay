# multimer types: queued, sync
# pyscript files: proverbs/__init__.py, proverbs/proverbs.py, proverbs/proverbs_20.py, proverbs/proverbs_30.py
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

import tft_write
import tft_config
from board_config import broker
from multimer import Timer, run_queued, sleep_ms

palette = tft_config.palette
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
    wheel = 0

    while True:
        for proverb in proverbs:
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
                    color_wheel(wheel),
                )

            wheel = (wheel + 5) % 256

            tft.show()
            if getattr(Timer, "REQUIRES_RUN_QUEUED", False):
                run_queued()
            broker.poll()
            sleep_ms(5000)


main()
