# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
from ._constants import ALIGN, PAD
from .widget import Widget


class _Layout(Widget):
    """
    Base for :class:`Row` / :class:`Column`: stacks children with fixed spacing.

    Not a full flexbox engine — children are laid out in insertion order along
    one axis (with a constant gap between them); the cross axis is left to each
    child's own alignment. Re-layout happens automatically whenever a child is
    added or removed.
    """

    _vertical = True

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
        spacing=PAD,
    ):
        self.spacing = spacing
        super().__init__(parent, x, y, w, h, align, align_to, fg, bg, visible, value, padding)

    def add_child(self, child):
        """Add a child widget, then re-flow the layout."""
        self.children.append(child)
        self._layout()
        child.invalidate()

    def remove_child(self, child):
        """Remove a child widget, then re-flow the layout."""
        self.children.remove(child)
        self._layout()
        self.invalidate()

    def _layout(self):
        """Position children sequentially along the layout axis."""
        offset = 0
        for child in self.children:
            if self._vertical:
                child.set_position(x=0, y=offset, align=ALIGN.TOP_LEFT, align_to=self)
                offset += child.height + self.spacing
            else:
                child.set_position(x=offset, y=0, align=ALIGN.TOP_LEFT, align_to=self)
                offset += child.width + self.spacing
