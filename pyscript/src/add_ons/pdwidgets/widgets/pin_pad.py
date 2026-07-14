# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""PinPad — numeric button grid emitting digits into a field / callback."""

from eventsys import events

from .._constants import ALIGN, PAD, TEXT_SIZE
from ..widget import Widget
from .button import Button
from .grid import Grid


class PinPad(Widget):
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
        value="",
        padding=None,
        target=None,
        on_digit=None,
        on_enter=None,
        max_length=8,
    ):
        """
        3x4 digit pad. Digits append to ``target.value`` (or ``on_digit``)
        and update ``self.value``.
        """
        self.target = target
        self.on_digit = on_digit
        self.on_enter = on_enter
        self.max_length = max_length
        bg = bg if bg is not None else parent.color_theme.surface
        fg = fg if fg is not None else parent.color_theme.on_surface
        w = w or parent.width
        h = h or 4 * (TEXT_SIZE.LARGE + 3 * PAD)
        super().__init__(parent, x, y, w, h, align, align_to, fg, bg, visible, value, padding)
        self.grid = Grid(self, columns=3, spacing=PAD, w=w, h=h, bg=bg)
        keys = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "C", "0", "OK"]
        cell_h = (h - 3 * PAD) // 4
        self.grid.cell_h = cell_h
        for key in keys:
            btn = Button(
                self.grid,
                label=key,
                h=cell_h,
                bg=self.color_theme.primary_variant
                if key == "OK"
                else self.color_theme.surface_variant,
                text_color=self.color_theme.on_primary if key == "OK" else self.fg,
                radius=6,
            )
            btn.add_event_cb(events.MOUSEBUTTONDOWN, self._make_key(key))

    def _make_key(self, key):
        def cb(data=None, event=None):
            if key == "C":
                self.value = ""
                if self.target is not None:
                    self.target.value = ""
            elif key == "OK":
                if self.on_enter:
                    self.on_enter(self.value)
            else:
                if self.max_length is None or len(self._value) < self.max_length:
                    self.value = (self._value or "") + key
                    if self.target is not None:
                        self.target.value = self.value
                    if self.on_digit:
                        self.on_digit(key, self.value)

        return cb
