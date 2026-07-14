# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
from .._constants import ALIGN, ICON_SIZE, PAD, TEXT_SIZE
from ..widget import Widget
from .label import Label


class FormRow(Widget):
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
        label="",
        scale=1,
        font=None,
    ):
        """
        A label-on-the-left row sized for a trailing control (Switch, Dropdown…).

        Create the row, then construct the control as a child of this row (it will
        be nudged to the right). Example::

            row = FormRow(card, label="Wi-Fi", y=y)
            Switch(row, align=ALIGN.RIGHT, value=True)

        ``ListTile`` is an alias of this class.
        """
        w = w or parent.width
        h = h or ICON_SIZE.LARGE + PAD
        fg = fg if fg is not None else parent.color_theme.on_surface
        bg = bg if bg is not None else parent.bg
        self.label_widget = None
        self.trailing = None
        self._layout_ready = False
        super().__init__(parent, x, y, w, h, align, align_to, fg, bg, visible, value, padding)
        self.label_widget = Label(
            self,
            value=label,
            x=PAD,
            align=ALIGN.LEFT,
            fg=fg,
            bg=bg,
            scale=scale,
            font=font,
            text_height=TEXT_SIZE.LARGE,
        )
        self._layout_ready = True

    def add_child(self, child):
        """Add a child; non-label children are treated as the trailing control."""
        super().add_child(child)
        if self._layout_ready and child is not self.label_widget:
            self.trailing = child
            child.set_position(align=ALIGN.RIGHT, x=-PAD, align_to=self)


ListTile = FormRow
