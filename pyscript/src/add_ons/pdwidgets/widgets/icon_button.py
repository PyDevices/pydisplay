# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
from .._constants import ALIGN
from ..widget import Widget
from .button import Button
from .icon import Icon


class IconButton(Button):
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
        icon_file=None,
    ):
        """
        Initialize an IconButton widget to display an icon on a button.

        Args:
            parent (Widget): The parent widget or screen that contains this icon button.
            x (int): The x-coordinate of the icon button.
            y (int): The y-coordinate of the icon button.
            w (int): The width of the icon button.
            h (int): The height of the icon button.
            align (int): The alignment of the icon button.
            align_to (Widget): The widget to align to.
            fg (int): The color of the icon button.
            bg (int): The background color of the icon button.
            visible (bool): The visibility of the icon button.
            value (str): The user-assigned value of the icon button.
            padding (tuple): The padding on each side of the icon button.
            icon_file (str): The icon file to display.

        Usage:
            icon_button = IconButton(screen, icon_file="icon.pbm")
        """
        fg = fg if fg is not None else parent.fg
        bg = bg if bg is not None else parent.bg
        self.icon = Icon(None, align=ALIGN.CENTER, fg=fg, bg=bg, value=icon_file)
        w = w or self.icon.width
        h = h or self.icon.height
        super().__init__(parent, x, y, w, h, align, align_to, fg, bg, visible, value, padding)
        self.icon.parent = self
