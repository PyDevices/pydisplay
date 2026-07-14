# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
from eventsys import events

from .._constants import ALIGN, ICON_SIZE, PAD, TEXT_SIZE
from .._themes import icon_theme
from ..widget import Widget
from .icon_button import IconButton
from .label import Label


class AppBar(Widget):
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
        value=None,
        padding=None,
        title="",
        on_back=None,
        scale=2,
        font=None,
    ):
        """
        Top title bar with optional back button.

        Args:
            parent (Widget): Usually the screen or a page.
            title (str): Title text drawn on the left (or after back).
            on_back (callable): If set, shows a leading back arrow that calls
                ``on_back(self)`` when pressed.
            bg (int): Defaults to ``primary``.
            fg (int): Defaults to ``on_primary``.
        """
        w = w or parent.width
        h = h or max(ICON_SIZE.LARGE + 2 * PAD, parent.height // 12)
        bg = bg if bg is not None else parent.color_theme.primary
        fg = fg if fg is not None else parent.color_theme.on_primary
        align = align if align is not None else ALIGN.TOP
        super().__init__(
            parent, x, y, w, h, align, align_to, fg, bg, visible, value, padding or (0, 0, 0, 0)
        )
        self.on_back = on_back
        self.back_button = None
        title_x = PAD * 2
        if on_back is not None:
            self.back_button = IconButton(
                self,
                align=ALIGN.LEFT,
                x=PAD,
                icon_file=icon_theme.left_arrow(ICON_SIZE.SMALL),
                fg=fg,
                bg=bg,
            )
            self.back_button.add_event_cb(events.MOUSEBUTTONDOWN, self._back)
            title_x = self.back_button.width + PAD

        self.title_label = Label(
            self,
            value=title,
            x=title_x,
            align=ALIGN.LEFT,
            fg=fg,
            bg=bg,
            scale=scale,
            font=font,
            text_height=TEXT_SIZE.LARGE,
        )

    def _back(self, data=None, event=None):
        if self.on_back:
            self.on_back(self)

    def set_title(self, title):
        """Update the title text."""
        self.title_label.set_value(title)
