# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
from .._constants import ICON_SIZE
from .._themes import icon_theme
from ..widget import Widget
from .toggle import Toggle


class ToggleButton(Toggle):
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
        Initialize a ToggleButton widget.

        Args:
            parent (Widget): The parent widget or screen that contains this toggle button.
            x (int): The x-coordinate of the toggle button.
            y (int): The y-coordinate of the toggle button.
            w (int): The width of the toggle button.
            h (int): The height of the toggle button.
            align (int): The alignment of the toggle button.
            align_to (Widget): The widget to align to.
            fg (int): The color of the toggle button.
            bg (int): The background color of the toggle button.
            visible (bool): The visibility of the toggle button.
            value (bool): The initial state of the toggle button.
            padding (tuple): The padding on each side of the toggle button.
            size (int): The size of the toggle button (default is ICON_SIZE.LARGE).

        Usage:
            toggle_button = ToggleButton(screen, size=ICON_SIZE.LARGE)
        """
        on_file = icon_theme.toggle_on(size)
        off_file = icon_theme.toggle_off(size)
        super().__init__(
            parent, x, y, w, h, align, align_to, fg, bg, visible, value, padding, on_file, off_file
        )
