# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
from eventsys import events

from .._constants import ICON_SIZE
from ..widget import Widget


class Switch(Widget):
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
        value=False,
        padding=None,
        on_color=None,
        off_color=None,
        knob_color=None,
    ):
        """
        Initialize a Switch: an iOS-style sliding on/off toggle.

        A rounded "pill" track with a circular knob that sits left (off) or
        right (on); tapping anywhere on it flips the state. This is a visual
        alternative to the icon-swapping :class:`ToggleButton`, built from the
        same cheap ``round_rect`` + ``circle`` primitives as :class:`Slider`.

        Args:
            parent (Widget): The parent widget or screen that contains this switch.
            x (int): The x-coordinate of the switch.
            y (int): The y-coordinate of the switch.
            w (int): The width of the switch (defaults to twice the height).
            h (int): The height of the switch.
            align (int): The alignment of the switch.
            align_to (Widget): The widget to align to.
            fg (int): The foreground color of the switch.
            bg (int): The background color behind the switch.
            visible (bool): The visibility of the switch.
            value (bool): The initial state (default False / off).
            padding (tuple): The padding on each side of the switch.
            on_color (int): Track color when on; defaults to ``success``.
            off_color (int): Track color when off; defaults to ``tertiary``.
            knob_color (int): Knob color; defaults to ``on_primary``.

        Usage:
            wifi = Switch(card, align=pd.ALIGN.RIGHT, value=True)
            wifi.set_change_cb(lambda s: print("wifi", s.value))
        """
        h = h or ICON_SIZE.MEDIUM
        w = w or h * 2
        self.on_color = on_color if on_color is not None else parent.color_theme.success
        self.off_color = off_color if off_color is not None else parent.color_theme.tertiary
        self.knob_color = knob_color if knob_color is not None else parent.color_theme.on_primary
        super().__init__(parent, x, y, w, h, align, align_to, fg, bg, visible, value, padding)

    def _register_callbacks(self):
        self.add_event_cb(events.MOUSEBUTTONDOWN, self.toggle)

    def toggle(self, data=None, event=None):
        """Flip the switch between on and off."""
        self.value = not self.value

    def draw(self, _=None):
        """Draw the pill track and the knob at the on/off position."""
        self.parent.draw(self.area)
        pa = self.padded_area
        r = pa.h // 2
        track = self.on_color if self.value else self.off_color
        self.display.framebuf.round_rect(*pa, r, track, f=True)
        knob_x = pa.x + pa.w - r if self.value else pa.x + r
        knob_r = r - 2 if r > 2 else r
        self.display.framebuf.circle(knob_x, pa.y + r, knob_r, self.knob_color, f=True)
