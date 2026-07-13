# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
from time import localtime

from ._constants import TEXT_SIZE, TEXT_WIDTH
from .label import Label
from .widget import Widget


class DigitalClock(Label):
    def __init__(
        self,
        parent: Widget,
        x=0,
        y=0,
        w=None,
        h=None,
        align=None,
        align_to=None,
        fg=None,
        bg=None,
        visible=True,
        value=None,
        padding=None,
        text_height=TEXT_SIZE.LARGE,
        scale=1,
    ):
        """
        Initialize a DigitalClock widget to display the current time.

        Args:
            parent (Widget): The parent widget or screen that contains this digital clock.
            x (int): The x-coordinate of the digital clock.
            y (int): The y-coordinate of the digital clock.
            w (int): The width of the digital clock.
            h (int): The height of the digital clock.
            align (int): The alignment of the digital clock.
            align_to (Widget): The widget to align to.
            fg (int): The color of the digital clock.
            bg (int): The background color of the digital clock.
            visible (bool): The visibility of the digital clock.
            value (str): The initial value of the digital clock.
            padding (tuple): The padding on each side of the digital clock.
            text_height (int): The height of the text (default is TEXT_SIZE.LARGE).
            scale (int): The scale of the text (default is 1).

        Usage:
            clock = DigitalClock(screen, text_height=TEXT_SIZE.LARGE, scale=2)
        """
        if text_height not in TEXT_SIZE:
            raise ValueError("Text height must be 8, 14 or 16 pixels.")
        fg = fg if fg is not None else parent.fg
        bg = bg if bg is not None else parent.bg
        w = w or (TEXT_WIDTH) * 8 * scale
        super().__init__(
            parent,
            x,
            y,
            w,
            h,
            align,
            align_to,
            fg,
            bg,
            visible,
            value,
            padding,
            text_height,
            scale,
        )
        self.task = self.display.add_task(self.update_time, 1000)

    def update_time(self):
        if self.visible:
            _y, _m, _d, h, min, sec, *_ = localtime()
            self.value = f"{h:02}:{min:02}:{sec:02}"
