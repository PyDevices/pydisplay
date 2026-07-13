# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
from ._constants import ICON_SIZE
from .widget import Widget


class ProgressBar(Widget):
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
        value=0.0,
        padding=None,
        vertical=False,
        reverse=False,
    ):
        """
        Initialize a ProgressBar widget to display a progress bar.

        Args:
            parent (Widget): The parent widget or screen that contains this progress bar.
            x (int): The x-coordinate of the progress bar.
            y (int): The y-coordinate of the progress bar.
            w (int): The width of the progress bar.
            h (int): The height of the progress bar.
            align (int): The alignment of the progress bar.
            align_to (Widget): The widget to align to.
            fg (int): The foreground color of the progress bar.
            bg (int): The background color of the progress bar.
            visible (bool): The visibility of the progress bar.
            value (float): The initial value of the progress bar (0 to 1).
            padding (tuple): The padding on each side of the progress bar.
            vertical (bool): Whether the progress bar is vertical (True) or horizontal (False).
            reverse (bool): Whether the progress bar is reversed (True) or not (False).

        Usage:
            progress_bar = ProgressBar(screen)
        """
        w = w or (ICON_SIZE.SMALL if vertical else ICON_SIZE.SMALL * 4)
        h = h or (ICON_SIZE.SMALL if not vertical else ICON_SIZE.SMALL * 4)
        fg = fg if fg is not None else parent.color_theme.on_primary
        bg = bg if bg is not None else parent.color_theme.primary_variant
        self.vertical = vertical
        self.reverse = reverse
        self.end_radius = w // 2 if self.vertical else h // 2
        super().__init__(parent, x, y, w, h, align, align_to, fg, bg, visible, value, padding)
        self.end_radius = self.padded_area.w // 2 if self.vertical else self.padded_area.h // 2

    def draw_ends(self):
        """
        Draw the circular ends of the progress bar.
        """
        pa = self.padded_area
        if self.vertical:
            self.display.framebuf.circle(
                pa.x + self.end_radius,
                pa.y + self.end_radius,
                self.end_radius,
                self.fg if self.reverse else self.bg,
                f=True,
            )
            self.display.framebuf.circle(
                pa.x + self.end_radius,
                pa.y + pa.h - self.end_radius,
                self.end_radius,
                self.fg if not self.reverse else self.bg,
                f=True,
            )
        else:
            self.display.framebuf.circle(
                pa.x + pa.w - self.end_radius,
                pa.y + self.end_radius,
                self.end_radius,
                self.fg if self.reverse else self.bg,
                f=True,
            )
            self.display.framebuf.circle(
                pa.x + self.end_radius,
                pa.y + self.end_radius,
                self.end_radius,
                self.fg if not self.reverse else self.bg,
                f=True,
            )

    def draw(self, _=None):
        """
        Draw the progress bar on the screen.
        """
        self.draw_ends()
        x, y, w, h = self.padded_area
        if self.vertical:
            y += self.end_radius
            h -= w
        else:
            x += self.end_radius
            w -= h
        self.display.framebuf.fill_rect(x, y, w, h, self.bg)

        if self.value == 0:
            return

        if self.vertical:
            progress_height = int(self.value * h)
            if self.reverse:
                self.display.framebuf.fill_rect(x, y, w, progress_height, self.fg)
            else:
                self.display.framebuf.fill_rect(
                    x, y + h - progress_height, w, progress_height, self.fg
                )
        else:
            progress_width = int(self.value * w)
            if self.reverse:
                self.display.framebuf.fill_rect(
                    x + w - progress_width, y, progress_width, h, self.fg
                )
            else:
                self.display.framebuf.fill_rect(x, y, progress_width, h, self.fg)

    def changed(self):
        # Ensure value is between 0 and 1
        if self.value < 0:
            self.value = 0
        elif self.value > 1:
            self.value = 1
        super().changed()
