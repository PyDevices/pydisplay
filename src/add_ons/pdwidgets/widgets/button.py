# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
from eventsys import events

from .._constants import ALIGN, ICON_SIZE, PAD, TEXT_SIZE, TEXT_WIDTH
from ..widget import Widget
from .icon import Icon
from .label import Label


class Button(Widget):
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
        radius=0,
        pressed_offset=2,
        pressed=False,
        label=None,
        text_color=None,
        text_height=TEXT_SIZE.LARGE,
        icon_file=None,
        icon_color=None,
        shadow=0,
    ):
        """
        Initialize a Button widget to display an icon and/or text.

        Args:
            parent (Widget): The parent widget or screen that contains this widget.
            x (int): The x-coordinate of the widget.
            y (int): The y-coordinate of the widget.
            w (int): The width of the widget.
            h (int): The height of the widget.
            align (int): The alignment of the widget.
            align_to (Widget): The widget to align to.
            fg (int): The foreground color of the widget.
            bg (int): The background color of the widget.
            visible (bool): The visibility of the widget (default is True).
            value (Any): User-assigned value of the widget.
            padding (tuple): The padding on each side of the widget.
            radius (int): The corner radius of the widget (default is 0).
            pressed_offset (int): The offset of the widget when pressed (default is 2).
            pressed (bool): The state of the widget (default is False).
            label (str): The text label of the widget.
            text_color (int): The color of the text label.
            text_height (int): The height of the text label (default is TEXT_SIZE.LARGE).
            icon_file (str): The icon file to display on the widget.
            icon_color (int): The color of the icon.
            shadow (int): Fake drop-shadow offset in pixels drawn behind the
                button in ``color_theme.shadow`` (0 disables; the default).
        """
        self.radius = radius
        self.pressed_offset = pressed_offset
        self.shadow = shadow
        self._pressed = pressed
        if w is None and label:
            w = (len(label) + 1) * TEXT_WIDTH + 2 * PAD
        w = w or ICON_SIZE.LARGE + 2 * PAD
        h = h or ICON_SIZE.LARGE + 2 * PAD
        bg = bg if bg is not None else parent.color_theme.primary_variant
        fg = fg if fg is not None else parent.color_theme.on_primary
        super().__init__(parent, x, y, w, h, align, align_to, fg, bg, visible, value, padding)
        if icon_file:
            icon_align = ALIGN.CENTER if not label else ALIGN.LEFT
            icon_color = icon_color if icon_color is not None else parent.color_theme.on_primary
            self.icon = Icon(self, align=icon_align, fg=icon_color, bg=self.bg, value=icon_file)
        if label:
            if text_height not in TEXT_SIZE:
                raise ValueError("Text height must be 8, 14 or 16 pixels.")
            label_align = ALIGN.CENTER if not icon_file else ALIGN.OUTER_RIGHT
            label_align_to = self.icon if icon_file else self
            text_color = text_color if text_color is not None else parent.color_theme.on_primary
            self.label = Label(
                self,
                value=label,
                align=label_align,
                align_to=label_align_to,
                fg=text_color,
                bg=self.bg,
                text_height=text_height,
            )
        else:
            self.label = None

    def _register_callbacks(self):
        self.add_event_cb(events.MOUSEBUTTONDOWN, self.press)
        self.add_event_cb(events.MOUSEBUTTONUP, self.release)

    def draw(self, _=None):
        """
        Draw the button background and shape (with an optional drop shadow).
        """
        self.parent.draw(self.area)
        pa = self.padded_area
        if self.shadow:
            # Cheap fake drop shadow: a shape-colored round_rect offset behind
            # the button. Two fills, no alpha blending.
            self.display.framebuf.round_rect(
                pa.x + self.shadow,
                pa.y + self.shadow,
                pa.w,
                pa.h,
                self.radius,
                self.color_theme.shadow,
                f=True,
            )
        self.display.framebuf.round_rect(*pa, self.radius, self.bg, f=True)

    def press(self, data=None, event=None):
        self._pressed = True
        self.display.framebuf.round_rect(*self.padded_area, self.radius, self.fg, f=False)
        self.display.refresh(self.area)

    def release(self, data=None, event=None):
        self._pressed = False
        self.display.framebuf.round_rect(*self.padded_area, self.radius, self.bg, f=False)
        self.display.refresh(self.area)
