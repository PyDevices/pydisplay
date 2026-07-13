# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
from .._constants import ICON_SIZE
from .._themes import icon_theme
from ..widget import Widget
from .toggle import Toggle


class CheckBox(Toggle):
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
        value=False,
        padding=None,
        size=ICON_SIZE.LARGE,
    ):
        """
        Initialize a CheckBox widget.

        Args:
            parent (Widget): The parent widget or screen that contains this check box.
            x (int): The x-coordinate of the check box.
            y (int): The y-coordinate of the check box.
            w (int): The width of the check box.
            h (int): The height of the check box.
            align (int): The alignment of the check box.
            align_to (Widget): The widget to align to.
            fg (int): The color of the check box.
            bg (int): The background color of the check box.
            visible (bool): The visibility of the check box.
            value (bool): The initial state of the check box.
            padding (tuple): The padding on each side of the check box.
            size (int): The size of the check box (default is ICON_SIZE.LARGE).

        Usage:
            check_box = CheckBox(screen, size=ICON_SIZE.LARGE)
        """
        on_file = icon_theme.check_box_checked(size)
        off_file = icon_theme.check_box_unchecked(size)
        super().__init__(
            parent, x, y, w, h, align, align_to, fg, bg, visible, value, padding, on_file, off_file
        )
