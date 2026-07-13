# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
from .._constants import ALIGN
from ..widget import Widget
from .scroll_bar import ScrollBar


class ListView(Widget):
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
        padding=None,
    ):
        """
        Initialize a ListView widget to display a list of items.

        Args:
            parent (Widget): The parent widget or screen that contains this list view.
            x (int): The x-coordinate of the list view.
            y (int): The y-coordinate of the list view.
            w (int): The width of the list view.
            h (int): The height of the list view.
            align (int): The alignment of the list view.
            align_to (Widget): The widget to align to.
            fg (int): The color of the list view.
            bg (int): The background color of the list view.
            visible (bool): The visibility of the list view.
            padding (tuple): The padding on each side of the list view.

        Usage:
            list_view = ListView(screen)
            button1 = Button(list_view, label="Button 1", value=1)
            button2 = Button(list_view, label="Button 2", value=2)
        """
        fg = fg if fg is not None else parent.color_theme.on_primary
        bg = bg if bg is not None else parent.color_theme.primary
        super().__init__(
            parent, x, y, w, h, align, align_to, fg, bg, visible, value=0, padding=padding
        )
        self.clip_content = True
        self.scrollbar = ScrollBar(
            parent,
            vertical=True,
            h=h,
            fg=fg,
            bg=bg,
            visible=False,
            align_to=self,
            align=ALIGN.OUTER_RIGHT,
        )
        self.scrollbar.slider.set_change_cb(self.scroll)

    def add_child(self, child: Widget):
        """Adds a child widget to the current widget."""
        self.children.append(child)
        self.reassign_positions()

    def remove_child(self, child: Widget):
        """Removes a child widget from the current widget."""
        self.children.remove(child)
        self.reassign_positions()

    def reassign_positions(self):
        """Reassign the positions of all children after one is removed."""
        self._value = min(self._value, len(self.children) - 1)
        for i, child in enumerate(self.children):
            child.visible = False
            if i == 0:
                child.set_position(0, 0, self.width, None, align=ALIGN.TOP_LEFT, align_to=self)
            else:
                child.set_position(
                    0,
                    child.height,
                    self.width,
                    None,
                    align=ALIGN.BOTTOM_LEFT,
                    align_to=self.children[i - 1],
                )
        self.config_scrollbar()

    def config_scrollbar(self):
        """Configure the scrollbar based on the number of children."""
        if len(self.children) > 1:
            self.scrollbar.slider.step = 1 / (len(self.children) - 1)
        self.changed()

    def scroll(self, sender):
        """Read the value of the scrollbar and scroll the list view accordingly."""
        self.value = int(self.scrollbar.slider.value * (len(self.children) - 1))

    def scroll_up(self):
        """Scroll the list view up by one item."""
        self.value -= 1

    def scroll_down(self):
        """Scroll the list view down by one item."""
        self.value += 1

    def changed(self):
        """Update the list view when the value changes."""
        if self.value < 0:
            self._value = 0
        elif self.value >= len(self.children):
            self._value = len(self.children) - 1

        for child in self.children:
            child.visible = False

        sb_visible = False
        if len(self.children):
            self.children[0].y = -sum([child.height for child in self.children[: self.value]])
            pad = self.padded_area
            for child in self.children:
                # Partial overlap is OK — clip_content hides overflow when drawing.
                if pad.intersects(child.area):
                    child.visible = True
                else:
                    child.visible = False
                if not pad.contains_area(child.area):
                    sb_visible = True
        self.scrollbar.visible = sb_visible
        if sb_visible and len(self.children) > 1:
            self.scrollbar.slider.value = self.value / (len(self.children) - 1)
        super().changed()
