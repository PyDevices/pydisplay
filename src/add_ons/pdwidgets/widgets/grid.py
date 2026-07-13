# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Grid — fixed-column cell layout (row-major)."""

from .._constants import ALIGN, PAD
from ..widget import Widget


class Grid(Widget):
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
        columns=2,
        spacing=PAD,
        cell_h=None,
    ):
        """Place children in a fixed-column grid in row-major order."""
        self.columns = max(1, int(columns))
        self.spacing = spacing
        self.cell_h = cell_h
        super().__init__(parent, x, y, w, h, align, align_to, fg, bg, visible, value, padding)

    def add_child(self, child):
        self.children.append(child)
        self._layout()
        child.invalidate()

    def remove_child(self, child):
        self.children.remove(child)
        self._layout()
        self.invalidate()

    def _layout(self):
        if not self.children:
            return
        cols = self.columns
        gap = self.spacing
        cell_w = (self.width - gap * (cols - 1)) // cols
        cell_h = self.cell_h or max(c.height for c in self.children)
        for i, child in enumerate(self.children):
            row, col = divmod(i, cols)
            child.set_position(
                x=col * (cell_w + gap),
                y=row * (cell_h + gap),
                w=cell_w,
                align=ALIGN.TOP_LEFT,
                align_to=self,
            )
