# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
from graphics import Area

from .display import Display
from .widget import Widget


class Screen(Widget):
    def __init__(self, parent: Display | Widget, fg=None, bg=None, visible=True):
        """
        Initialize a Screen object to contain widgets.

        Args:
            parent (Display): The display object that contains the screen.
            fg (int): The foreground color of the screen.
            bg (int): The background color of the screen.
            visible (bool): The visibility of the screen.

        Usage:
            screen = Screen(display)
        """
        super().__init__(
            parent,
            0,
            0,
            parent.width,
            parent.height,
            fg=fg,
            bg=bg,
            visible=visible,
            padding=(0, 0, 0, 0),
        )
        self.partitioned = self.display.tfa > 0 or self.display.bfa > 0

        if self.partitioned:
            self.top = Widget(
                self,
                *Area(self.display.tfa_area),
                fg=parent.color_theme.on_primary,
                bg=parent.color_theme.primary,
            )
            self.main = Widget(self, *Area(self.display.vsa_area))
            self.bottom = Widget(
                self,
                *Area(self.display.bfa_area),
                fg=parent.color_theme.on_primary,
                bg=parent.color_theme.primary,
            )
