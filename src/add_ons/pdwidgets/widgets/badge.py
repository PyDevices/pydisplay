# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
from ._constants import PAD, TEXT_SIZE, TEXT_WIDTH
from .widget import Widget


class Badge(Widget):
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
        size=12,
    ):
        """
        Initialize a Badge: a small colored status dot or count pill.

        With no ``value`` the badge is a filled dot (useful as a connection or
        status indicator); with a short ``value`` (e.g. a notification count) it
        becomes a rounded pill containing the text.

        Args:
            parent (Widget): The parent widget or screen that contains this badge.
            x (int): The x-coordinate of the badge.
            y (int): The y-coordinate of the badge.
            w (int): The width of the badge (auto-sized when omitted).
            h (int): The height of the badge (auto-sized when omitted).
            align (int): The alignment of the badge.
            align_to (Widget): The widget to align to.
            fg (int): The text color; defaults to ``on_error``.
            bg (int): The badge color; defaults to ``error``.
            visible (bool): The visibility of the badge.
            value (Any): Optional short text/count; ``None`` draws a plain dot.
            padding (tuple): The padding on each side of the badge.
            size (int): Diameter (dot) or height (pill) in pixels (default 12).

        Usage:
            online = Badge(bar, bg=screen.color_theme.success)  # status dot
            unread = Badge(icon, value=3, align=pd.ALIGN.OUTER_TOP_RIGHT)  # pill
        """
        bg = bg if bg is not None else parent.color_theme.error
        fg = fg if fg is not None else parent.color_theme.on_error
        padding = padding if padding is not None else (0, 0, 0, 0)
        self.size = size
        text = "" if value is None else str(value)
        if text:
            w = w or max(size, len(text) * TEXT_WIDTH + PAD * 3)
            h = h or size
        else:
            w = w or size
            h = h or size
        super().__init__(parent, x, y, w, h, align, align_to, fg, bg, visible, value, padding)

    def draw(self, _=None):
        """Draw the badge as a dot (no value) or a rounded pill (with text)."""
        self.parent.draw(self.area)
        pa = self.padded_area
        text = "" if self._value is None else str(self._value)
        if text:
            self.display.framebuf.round_rect(*pa, pa.h // 2, self.bg, f=True)
            tx = pa.x + (pa.w - len(text) * TEXT_WIDTH) // 2
            ty = pa.y + (pa.h - TEXT_SIZE.SMALL) // 2
            self.display.framebuf.text(text, tx, ty, self.fg, height=TEXT_SIZE.SMALL)
        else:
            r = pa.h // 2
            self.display.framebuf.circle(pa.x + r, pa.y + r, r, self.bg, f=True)
