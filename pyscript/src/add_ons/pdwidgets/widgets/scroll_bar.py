# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
from eventsys import events

from .._constants import ALIGN, ICON_SIZE
from .._themes import icon_theme
from ..widget import Widget
from .icon_button import IconButton
from .slider import Slider


class ScrollBar(Widget):
    def __init__(  # noqa: PLR0913
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
        value=0.0,
        padding=None,
        vertical=False,
        reverse=False,
        knob_color=None,
        step=0.1,
    ):
        """
        Initialize a ScrollBar widget with two arrow IconButtons and a Slider.

        Args:
            parent (Widget): The parent widget or screen that contains this scroll bar.
            x (int): The x-coordinate of the scroll bar.
            y (int): The y-coordinate of the scroll bar.
            w (int): The width of the scroll bar.
            h (int): The height of the scroll bar.
            align (int): The alignment of the scroll bar.
            align_to (Widget): The widget to align to.
            fg (int): The foreground color of the scroll bar.
            bg (int): The background color of the scroll bar.
            visible (bool): The visibility of the scroll bar.
            value (float): The initial value of the scroll bar (0 to 1).
            padding (tuple): The padding on each side of the scroll bar.
            vertical (bool): Whether the scroll bar is vertical (True) or horizontal (False).
            reverse (bool): Whether the scroll bar is reversed (True) or not (False).
            knob_color (int): The color of the knob.
            step (float): The step size for value adjustments.

        Usage:
            scroll_bar = ScrollBar(screen, vertical=True, step=0.1)
        """

        if vertical:
            w = w or ICON_SIZE.SMALL
            h = h or parent.height if parent else 6 * ICON_SIZE.SMALL
            align = align if align is not None else ALIGN.RIGHT
            icon_size = w
        else:
            w = w or parent.width if parent else 6 * ICON_SIZE.SMALL
            h = h or ICON_SIZE.SMALL
            align = align if align is not None else ALIGN.BOTTOM
            icon_size = h
        reverse = (
            not reverse if vertical else reverse
        )  # Reverse the direction for vertical sliders
        super().__init__(parent, x, y, w, h, align, align_to, fg, bg, visible, value, padding)

        # Add IconButton on each end and Slider in the middle
        if vertical:
            self.pos_button = IconButton(
                self,
                w=icon_size,
                h=icon_size,
                icon_file=icon_theme.up_arrow(ICON_SIZE.SMALL),
                fg=fg,
                bg=bg,
                align=ALIGN.TOP,
            )
            self.neg_button = IconButton(
                self,
                w=icon_size,
                h=icon_size,
                icon_file=icon_theme.down_arrow(ICON_SIZE.SMALL),
                fg=fg,
                bg=bg,
                align=ALIGN.BOTTOM,
            )
            self.slider = Slider(
                self,
                w=icon_size,
                h=h - 2 * icon_size,
                vertical=True,
                align=ALIGN.CENTER,
                value=value,
                step=step,
                reverse=reverse,
                knob_color=knob_color,
                fg=fg,
                bg=bg,
            )
        else:
            self.neg_button = IconButton(
                self,
                w=icon_size,
                h=icon_size,
                icon_file=icon_theme.left_arrow(ICON_SIZE.SMALL),
                fg=fg,
                bg=bg,
                align=ALIGN.LEFT,
            )
            self.pos_button = IconButton(
                self,
                w=icon_size,
                h=icon_size,
                icon_file=icon_theme.right_arrow(ICON_SIZE.SMALL),
                fg=fg,
                bg=bg,
                align=ALIGN.RIGHT,
            )
            self.slider = Slider(
                self,
                w=w - icon_size * 2,
                h=icon_size,
                vertical=False,
                align=ALIGN.CENTER,
                value=value,
                step=step,
                reverse=reverse,
                knob_color=knob_color,
                fg=fg,
                bg=bg,
            )

        # Set button callbacks to adjust slider value
        self.neg_button.add_event_cb(
            events.MOUSEBUTTONDOWN, lambda _, e: self.slider.adjust_value(-self.slider.step)
        )
        self.pos_button.add_event_cb(
            events.MOUSEBUTTONDOWN, lambda _, e: self.slider.adjust_value(self.slider.step)
        )
