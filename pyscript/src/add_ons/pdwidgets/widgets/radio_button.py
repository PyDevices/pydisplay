# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
from .._constants import ICON_SIZE
from .._themes import icon_theme
from ..widget import Widget
from .radio_group import RadioGroup
from .toggle import Toggle


class RadioButton(Toggle):
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
        group: RadioGroup = None,
    ):
        """
        Initialize a RadioButton widget.

        Args:
            parent (Widget): The parent widget or screen that contains this radio button.
            x (int): The x-coordinate of the radio button.
            y (int): The y-coordinate of the radio button.
            w (int): The width of the radio button.
            h (int): The height of the radio button.
            align (int): The alignment of the radio button.
            align_to (Widget): The widget to align to.
            fg (int): The color of the radio button.
            bg (int): The background color of the radio button.
            visible (bool): The visibility of the radio button.
            value (bool): The initial state of the radio button.
            padding (tuple): The padding on each side of the radio button.
            size (int): The size of the radio button (default is ICON_SIZE.LARGE).
            group (RadioGroup): The RadioGroup to which this radio button belongs.

        Usage:
            radio_group = RadioGroup()
            radio_button = RadioButton(screen, group=radio_group)
        """
        if group is None:
            raise ValueError("RadioButton must be part of a RadioGroup.")
        self.group = group
        self.group.add(self)
        on_file = icon_theme.radio_button_checked(size)
        off_file = icon_theme.radio_button_unchecked(size)
        super().__init__(
            parent, x, y, w, h, align, align_to, fg, bg, visible, value, padding, on_file, off_file
        )

    def toggle(self, data=None, event=None):
        """Toggle the checked state to true when clicked and uncheck other RadioButtons in the group."""
        if not self.value:  # Only toggle if not already checked
            self.group.set_checked(self)  # Uncheck all other buttons in the group
