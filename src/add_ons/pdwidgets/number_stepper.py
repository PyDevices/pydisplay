# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
from eventsys import events

from ._constants import ALIGN, ICON_SIZE, PAD
from ._themes import icon_theme
from .icon_button import IconButton
from .text_box import TextBox
from .widget import Widget


class NumberStepper(Widget):
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
        value=0,
        padding=None,
        step=1,
        minimum=None,
        maximum=None,
        number_format="{}",
    ):
        """
        Initialize a NumberStepper: a ``-`` button, a value display and a ``+``
        button for adjusting a bounded number.

        This generalizes the ad-hoc ``+``/``-`` :class:`IconButton` pattern into
        a reusable widget. Pressing a button changes ``value`` by ``step``,
        clamped to ``[minimum, maximum]`` when those are given, and fires the
        change callback.

        Args:
            parent (Widget): The parent widget or screen that contains this stepper.
            x (int): The x-coordinate of the stepper.
            y (int): The y-coordinate of the stepper.
            w (int): The width of the stepper.
            h (int): The height of the stepper.
            align (int): The alignment of the stepper.
            align_to (Widget): The widget to align to.
            fg (int): The value-text color; defaults to ``on_surface``.
            bg (int): The background color; defaults to ``surface_variant``.
            visible (bool): The visibility of the stepper.
            value (int | float): The initial value (default 0).
            padding (tuple): The padding on each side of the stepper.
            step (int | float): Amount added/subtracted per press (default 1).
            minimum (int | float): Lower clamp bound, or ``None`` for unbounded.
            maximum (int | float): Upper clamp bound, or ``None`` for unbounded.
            number_format (str): ``str.format`` spec for the value display.

        Usage:
            temp = NumberStepper(card, value=20, minimum=15, maximum=30)
            temp.set_change_cb(lambda s: print("set", s.value))
        """
        h = h or ICON_SIZE.LARGE + 2 * PAD
        w = w or ICON_SIZE.LARGE * 4
        bg = bg if bg is not None else parent.color_theme.surface_variant
        fg = fg if fg is not None else parent.color_theme.on_surface
        self.step = step
        self.minimum = minimum
        self.maximum = maximum
        self._number_format = number_format
        super().__init__(parent, x, y, w, h, align, align_to, fg, bg, visible, value, padding)
        btn_w = self.padded_area.h
        btn_h = self.padded_area.h
        self.neg_button = IconButton(
            self,
            w=btn_w,
            h=btn_h,
            align=ALIGN.LEFT,
            icon_file=icon_theme.remove(ICON_SIZE.SMALL),
            fg=parent.color_theme.on_primary,
            bg=parent.color_theme.primary_variant,
        )
        self.pos_button = IconButton(
            self,
            w=btn_w,
            h=btn_h,
            align=ALIGN.RIGHT,
            icon_file=icon_theme.add(ICON_SIZE.SMALL),
            fg=parent.color_theme.on_primary,
            bg=parent.color_theme.primary_variant,
        )
        self.box = TextBox(
            self,
            w=self.width - 2 * btn_w,
            align=ALIGN.CENTER,
            value=number_format.format(value),
            fg=fg,
            bg=bg,
            format="^",
        )
        self.neg_button.add_event_cb(events.MOUSEBUTTONDOWN, lambda d, e: self._step(-1))
        self.pos_button.add_event_cb(events.MOUSEBUTTONDOWN, lambda d, e: self._step(1))

    def _step(self, direction):
        """Adjust the value by ``step`` in the given direction (+1 / -1)."""
        self.value = self._value + self.step * direction

    def changed(self):
        """Clamp the value to the configured bounds and refresh the display."""
        v = self._value
        if self.minimum is not None and v < self.minimum:
            v = self.minimum
        if self.maximum is not None and v > self.maximum:
            v = self.maximum
        self._value = v
        self.box.value = self._number_format.format(v)
        super().changed()
