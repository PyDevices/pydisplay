# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
from eventsys import events

from ..widget import Widget
from .icon_button import IconButton


class Toggle(IconButton):
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
        on_file=None,
        off_file=None,
    ):
        """
        An IconButton that toggles between two states (on and off).  Serves as a base widget for
        ToggleButton, CheckBox, and RadioButton widgets but may be used on its own.  Requires an
        on_file and optionally an off_file.  If only a single file is provided, the widget will
        change colors when toggled, otherwise the icon will change.

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
            on_file (str): The icon file to display when the button is on.
            off_file (str): The icon file to display when the button is off.

        Usage:
            toggle = Toggle(screen, on_file="on.pbm", off_file="off.pbm")
        """
        if not on_file:
            raise ValueError("An on_file file must be provided.")
        self.on_file = on_file
        self.off_file = off_file
        icon_file = self.off_file if self.off_file and not value else self.on_file
        super().__init__(
            parent, x, y, w, h, align, align_to, fg, bg, visible, value, padding, icon_file
        )
        self.changed()

    def _register_callbacks(self):
        self.add_event_cb(events.MOUSEBUTTONDOWN, self.toggle)

    def toggle(self, data=None, event=None):
        """Toggle the on/off state of the button."""
        self.value = not self.value  # Invert the current state

    def changed(self):
        """Update the icon based on the current on/off state."""
        # Update the icon value based on the current toggle state
        if self.off_file:
            self.icon.value = self.on_file if self.value else self.off_file
        else:
            self.icon.fg = self.fg if self.value else self.color_theme.tertiary
        super().changed()  # Call the parent changed method
