# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
from .._constants import PAD
from ..widget import Widget


class Divider(Widget):
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
        thickness=1,
    ):
        """
        A thin horizontal rule used to separate sections in cards and lists.

        Args:
            parent (Widget): Parent container.
            thickness (int): Line height in pixels (default 1).
            fg (int): Line color; defaults to ``outline``.
        """
        h = h or max(1, thickness) + 2 * PAD
        fg = fg if fg is not None else parent.color_theme.outline
        bg = bg if bg is not None else parent.bg
        self.thickness = max(1, thickness)
        super().__init__(parent, x, y, w, h, align, align_to, fg, bg, visible, value, padding)

    def draw(self, _=None):
        """Paint the parent background, then the centered hairline."""
        self.parent.draw(self.area)
        pa = self.padded_area
        y = pa.y + (pa.h - self.thickness) // 2
        self.display.framebuf.fill_rect(pa.x, y, pa.w, self.thickness, self.fg)
